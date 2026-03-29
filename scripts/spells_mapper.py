import re
import os
import sys
import time
from lxml import etree

from xml_validator import validate_xml
from slug_generator import generate_slug

# ==========================================
# CONFIGURATION & CONSTANTES
# ==========================================

MULTI_WORD_TRAITS = [
    "NON LÉTAL", 
    "PEU COURANT", 
    "MISE HORS DE COMBAT",
    "TOUR DE MAGIE"
]

# Plage stricte des majuscules (exclut les minuscules accentuées)
UPPER = r'A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ'

# ==========================================
# PRÉ-NETTOYAGE DU PDF
# ==========================================

def clean_pdf_artifacts(content):
    """Purge les filigranes, numéros de page et sommaires avant traitement."""
    # 1. Gestion des retours à la ligne litéraux
    content = content.replace('\\n', '\n')
    
    # 2. Purge des en-têtes/pieds de page et filigranes
    content = re.sub(r'\[\[PAGE \d+\]\]', '', content)
    #content = re.sub(r'(?m)^\s*\d+\s*$', '', content)
    content = re.sub(r'(?m)^\s*Sorts\s*$', '', content, flags=re.IGNORECASE)
    content = re.sub(r'(?m)^\s*# FLUX PRINCIPAL \(STATS/BASE\)\s*$\n*\s*\d{1,3}', '', content)
    content = re.sub(r'(?m)^.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}.*$\n?', '', content)
    
    # 3. Suppression intelligente des sommaires (barres latérales)
    lines = content.split('\n')
    cleaned_lines = []
    streak = []
    
    for line in lines:
        stripped = line.strip()
        # Si la ligne est courte et ne ressemble pas à un titre de sort
        if 0 < len(stripped) < 25 and not re.search(r'\b(?:SORT|TOUR DE MAGIE)\s+\d+', stripped):
            streak.append(line)
        elif len(stripped) == 0:
            streak.append(line)
        else:
            if len([l for l in streak if l.strip()]) >= 5:
                pass # C'était un sommaire, on l'ignore
            else:
                cleaned_lines.extend(streak)
            cleaned_lines.append(line)
            streak = []
            
    if len([l for l in streak if l.strip()]) < 5:
        cleaned_lines.extend(streak)
        
    return '\n'.join(cleaned_lines)

# ==========================================
# UTILITAIRES
# ==========================================

def clean_text(text):
    if not text: return ""
    #text = text.replace("-\n", "").replace("- ", "")
    text = re.sub(r'-\n?\s+', '', text)  # Nettoie les résidus de mots coupés
    # text = re.sub(r'-\s+', '', text)  # Nettoie les résidus de mots coupés

    return re.sub(r'\s+', ' ', text).strip()

def clean_value(val):
    if not val: return None
    return re.sub(r'^[:\-\s]+', '', clean_text(val)).strip()

def parse_traits(traits_raw):
    text = traits_raw.upper().strip()
    final_traits = []
    for multi in MULTI_WORD_TRAITS:
        if multi in text:
            final_traits.append(multi)
            text = text.replace(multi, "")
            
    for t in text.split():
        t_clean = re.sub(r'[^A-ZÀ-Ÿ]', '', t)
        if len(t_clean) > 1: 
            final_traits.append(t_clean)
    return final_traits

def add_rich_text(parent, text_content, tag_name=None):
    """Génère un nœud XML en convertissant les *mot* en balises <spell>mot</spell>"""
    if not text_content: return
    
    if tag_name is None:
        el = parent
    else:
        el = etree.SubElement(parent, tag_name)

    # Accepte n'importe quel caractère (y compris la ponctuation) sauf un astérisque
    parts = re.split(r'(?<!\*)\*([^\*]+?)\*(?!\*)', text_content)
    
    el.text = parts[0]
    for i in range(1, len(parts), 2):
        spell_el = etree.SubElement(el, "spellRef")
        spell_el.text = parts[i]
        if i + 1 < len(parts):
            spell_el.tail = parts[i+1]
# ==========================================
# PARSING D'UN BLOC DE SORT
# ==========================================

def parse_spell_block(content):
    spell_data = {'savingThrows': {}, 'heightened': []}
    
# 1. En-tête (Nom) - Utilise la nouvelle constante UPPER
    name_regex = rf'^\s*\**([{UPPER}][{UPPER}\s\-\'’]+)(?:(?:\*{{2}}(?:\s|$))|(?:SORT|TOUR DE MAGIE))'
    name_match = re.search(name_regex, content, re.MULTILINE)
    spell_data['name'] = clean_text(name_match.group(1)) if name_match else "INCONNU"

    # 2. Rang (Gère Sort et Tour de Magie)
    rank_match = re.search(r'\b(SORT|TOUR DE MAGIE)\s+(\d+)', content)
    spell_data['type'] = rank_match.group(1)
    spell_data['rank'] = rank_match.group(2) if rank_match else "1"

    # 3. Actions (Isolé entre le Nom et le Rang)
    header_end = rank_match.end() if rank_match else 200
    header_area = content[:header_end]
    action_match = re.search(r'(?m)^\s*\**\s*([123R])\s*\**\s*$', header_area)
    if not action_match:
        action_match = re.search(r'\b(1|2|3|R)\b', header_area[name_match.end() if name_match else 0:])
    spell_data['actions'] = action_match.group(1) if action_match else None

    # 4. Mécaniques stricto sensu (Bloque au premier saut de ligne ou point-virgule)
    mech_prefix = r'(?:(?<=\n)|(?<=;)|(?<=^))\s*\**'
    mechanics = {
        'range': mech_prefix + r'Portée\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'targets': mech_prefix + r'Cibles?\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'defense': mech_prefix + r'Défense\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'duration': mech_prefix + r'Durée\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'area': mech_prefix + r'Zone[\s:]*\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'cast': mech_prefix + r'Incantation\**[\s:]*(.*?)(?=\s*(?:;|\n|$))'
    }
    
    mech_ends = []
    for key, pattern in mechanics.items():
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            spell_data[key] = clean_value(m.group(1))
            mech_ends.append(m.end())
        else:
            spell_data[key] = None

    # 5. Traditions
    trad_match = re.search(mech_prefix + r'Traditions?\**[\s:]*([a-zA-Zà-ÿ,\s]+?)(?=\s*(?:;|\n|$))', content, re.IGNORECASE)
    if trad_match:
        spell_data['traditions'] = [clean_value(t).lower() for t in trad_match.group(1).split(',')]
        mech_ends.append(trad_match.end())
    else:
        spell_data['traditions'] = []

    # 6. Traits (Entre le Rang et la première mécanique)
    first_mech_start = min([m.start() for m in re.finditer(r'(?:(?<=\n)|(?<=;)|(?<=^))\s*\**(?:Portée|Cibles?|Défense|Durée|Zone|Incantation|Traditions?)', content, re.IGNORECASE)] or [len(content)])
    traits_area = content[header_end:first_mech_start]
    spell_data['traits'] = parse_traits(traits_area)

    # 7. Sauvegardes
    save_patterns = {
        'criticalSuccess': r'(?:^|\n)\s*\**Succès critique\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Succès|Échec|Intensifié)|$)',
        'success': r'(?:^|\n)\s*\**Succès\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Succès|Échec|Intensifié)|$)',
        'failure': r'(?:^|\n)\s*\**Échec\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Échec|Intensifié)|$)',
        'criticalFailure': r'(?:^|\n)\s*\**Échec critique\.?\s?\**[\s]*(.*?)(?=\n\s*\**(?:Intensifié)|$)'
    }
    for key, pattern in save_patterns.items():
        m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if m: spell_data['savingThrows'][key] = clean_text(m.group(1))

    # 8. Intensification - Ajout d'un \s* pour tolérer l'espace avant les **
    h_pattern = r'(?:^|\n)\s*\**Intensifiés?\s*\((.*?)\)\.?\s*\**\s*(.*?)(?=(?:\n\s*\**Intensifié)|$)'
    for m in re.finditer(h_pattern, content, re.DOTALL | re.IGNORECASE):
        type_val = re.sub(r'[\*]', '', m.group(1)).strip()
        spell_data['heightened'].append({
            "type": type_val,
            "text": clean_text(m.group(2))
        })

    # 9. Description (Démarre après la dernière mécanique, s'arrête avant la première sauvegarde)
    desc_start = max(mech_ends) if mech_ends else header_end
    
    save_starts = []
    for p in save_patterns.values():
        m = re.search(p, content, re.DOTALL | re.IGNORECASE)
        if m: save_starts.append(m.start())
    for m in re.finditer(h_pattern, content, re.DOTALL | re.IGNORECASE):
        save_starts.append(m.start())
        
    desc_end = min(save_starts) if save_starts else len(content)
    spell_data['description'] = clean_text(content[desc_start:desc_end])

    return spell_data

# ==========================================
# PARSING COMPLET DES SORTS
# ==========================================

def parse_spells_md(content):
    """Extrait et parse tous les sorts du Markdown brut."""
    spells_data = []
    print("[PARSING] Début de l'analyse des sorts...")

    # Nettoyage
    content = '\n' + clean_pdf_artifacts(content).strip()

    # Découpage robuste avec la constante UPPER pour éviter de couper sur un "é"
    split_regex = rf'\n(?=\s*\**[{UPPER}][{UPPER}\s\-\'’]+\s?\**\s*(?:.{{0,150}}?)\b(?:SORT|TOUR DE MAGIE)\s+\d+)'
    split_pattern = re.compile(split_regex, re.DOTALL)
    spell_blocks = split_pattern.split(content)
    
    spell_blocks = [b for b in spell_blocks if "SORT" in b or "TOUR DE MAGIE" in b]

    print(f"[PARSING] {len(spell_blocks)} sorts isolés.")

    for block in spell_blocks:
        data = parse_spell_block(block)
        spells_data.append(data)
        print(f"[PARSING]   ✓ {data['name']}")

    return spells_data

# ==========================================
# GÉNÉRATION XML
# ==========================================

def generate_spells_xml(spells_data, output_path):
    """Transforme la liste des sorts en fichier XML."""
    start_time = time.time()
    print("[XML] Début de la génération du fichier XML...")
    
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    root = etree.Element("spells", nsmap={'xsi': XSI_NS})
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../xslt/spell.xsd")

    for data in spells_data:
        # Génération de l'ID dynamique
        trait_id = generate_slug("spell", data['name'])
        s_el = etree.SubElement(root, "spell", id=trait_id)

        etree.SubElement(s_el, "name").text = data['name']

        if data['type']: 
            etree.SubElement(s_el, "type").set('type',"spell" if data['type']=="SORT" else "cantrip" if data['type']=="TOUR DE MAGIE" else "unknown")
        etree.SubElement(s_el, "rank").text = data['rank']
        if data['actions']: etree.SubElement(s_el, "actions").text = data['actions']
        
        if data.get('traits'):
            t_el = etree.SubElement(s_el, "traits")
            for t in data['traits']:
                etree.SubElement(t_el, "trait").text = t
        
        if data.get('traditions'):
            tr_el = etree.SubElement(s_el, "traditions")
            for tr in data['traditions']:
                etree.SubElement(tr_el, "tradition").text = tr

        for field in ['cast', 'range', 'area', 'targets', 'defense', 'duration']:
            if data.get(field): etree.SubElement(s_el, field).text = data[field]
        
        add_rich_text(s_el, data['description'], "description")

        if data['savingThrows']:
            st_el = etree.SubElement(s_el, "savingThrow")
            for k in ['criticalSuccess', 'success', 'failure', 'criticalFailure']:
                if k in data['savingThrows']:
                    add_rich_text(st_el, data['savingThrows'][k], k)

        if data['heightened']:
            hl_el = etree.SubElement(s_el, "heightenList")
            for h in data['heightened']:
                el = etree.SubElement(hl_el, "heighten", type=h['type'])
                add_rich_text(el, h['text'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
    
    total_time = time.time() - start_time
    print(f"[XML] ✓ Fichier sauvegardé à {output_path} - {total_time:.3f}s")

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/subset_1/sorts_MD.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./data/spells/all_spells.xml"

    print("="*60)
    print("DÉBUT DU TRAITEMENT (SPELLS MAPPER)")
    print("="*60 + "\n")

    start_total = time.time()

    if os.path.exists(input_file):
        print(f"[MAIN] Lecture du fichier {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"[MAIN] ✓ Fichier chargé ({len(md_content)} caractères)\n")

        spells_data = parse_spells_md(md_content)
        generate_spells_xml(spells_data, output_file)
        
        print(f"[MAIN] ✓ Succès ! Le fichier {output_file} a été généré.")

        xsd_file = "./xslt/spell.xsd"
        if os.path.exists(output_file) and os.path.exists(xsd_file):
            validate_xml(output_file, xsd_file)
        else:
            print(f"[WARNING] Fichier XSD introuvable ({xsd_file}), validation ignorée.")
    else:
        print(f"[MAIN] ✗ Erreur : le fichier {input_file} n'existe pas.")

    total_elapsed = time.time() - start_total
    print(f"\n[MAIN] Temps total de traitement: {total_elapsed:.3f}s")
    print("="*60)