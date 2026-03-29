import re
import os
import sys
from lxml import etree

# ==========================================
# CONFIGURATION & CONSTANTES
# ==========================================

MULTI_WORD_TRAITS = [
    "NON LÉTAL", 
    "PEU COURANT", 
    "MISE HORS DE COMBAT"
]

# ==========================================
# PRÉ-NETTOYAGE DU PDF
# ==========================================

def clean_pdf_artifacts(content):
    """Purge les filigranes, numéros de page et sommaires avant traitement."""
    # 1. Gestion des retours à la ligne litéraux qui font tout planter
    content = content.replace('\\n', '\n')
    
    # 2. Numéros de page et balises type [[PAGE 1]]
    content = re.sub(r'\[\[PAGE \d+\]\]', '', content)
    content = re.sub(r'(?m)^\s*\d+\s*$', '', content)
    
    # 3. Filigranes et adresses mail (Toute ligne contenant un @ avec un domaine)
    content = re.sub(r'(?m)^.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}.*$\n?', '', content)
    
    # 4. Suppression intelligente des sommaires / barres latérales
    lines = content.split('\n')
    cleaned_lines = []
    streak = []
    
    for line in lines:
        stripped = line.strip()
        # Ligne courte (< 25 chars) qui ne ressemble pas au header "SORT X"
        if 0 < len(stripped) < 25 and not re.search(r'\bSORT\s+\d+', stripped):
            streak.append(line)
        elif len(stripped) == 0:
            streak.append(line)
        else:
            # Ligne normale -> on casse la série
            if len([l for l in streak if l.strip()]) >= 5:
                pass # C'était un sommaire, on l'efface
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
    text = text.replace("-\n", "").replace("- ", "")
    return re.sub(r'\s+', ' ', text).strip()

def clean_value(val):
    if not val: return None
    val = clean_text(val)
    return re.sub(r'^[:\-\s]+', '', val).strip()

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

# ==========================================
# PARSING D'UN BLOC DE SORT
# ==========================================

def parse_spell_block(content):
    spell_data = {'savingThrows': {}, 'heightened': []}
    
    # 1. En-tête (Nom) - Prend la première ligne pleine en MAJUSCULES
    name_match = re.search(r'^\s*\**([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-\'’]+)\**(?:\s|$)', content, re.MULTILINE)
    spell_data['name'] = clean_text(name_match.group(1)) if name_match else "INCONNU"

    # 2. Rang (SORT X)
    rank_match = re.search(r'\bSORT\s+(\d+)', content)
    spell_data['rank'] = rank_match.group(1) if rank_match else "1"

    # 3. Actions 
    header_area = content[:content.find('SORT')] if 'SORT' in content else content[:200]
    action_match = re.search(r'(?:\b|^|\s)(1|2|3|R)(?:\b|\s|$)', header_area)
    spell_data['actions'] = action_match.group(1) if action_match else None

    # 4. Mécaniques (Stoppe la capture si on croise un autre champ)
    stop_words = r'(?=\bCibles?\b|\bDéfense\b|\bDurée\b|\bZone\b|\bPortée\b|\bIncantation\b|;|\n|$)'
    mechanics = {
        'range': r'\**?Portée\**[\s:]*(.*?)' + stop_words,
        'targets': r'\**?Cibles?\**[\s:]*(.*?)' + stop_words,
        'defense': r'\**?Défense\**[\s:]*(.*?)' + stop_words,
        'duration': r'\**?Durée\**[\s:]*(.*?)' + stop_words,
        'area': r'\**?Zone[\s:]*\**[\s:]*(.*?)' + stop_words,
        'cast': r'\**?Incantation\**[\s:]*(.*?)' + stop_words
    }
    
    end_of_mechanics = name_match.end() if name_match else 0
    for key, pattern in mechanics.items():
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            spell_data[key] = clean_value(m.group(1))
            if m.end() > end_of_mechanics: end_of_mechanics = m.end()
        else:
            spell_data[key] = None

    # 5. Traditions
    trad_match = re.search(r'\*?Traditions?\**[\s:]*([a-zA-Zà-ÿ,\s]+?)(?=\n|\*|;)', content, re.IGNORECASE)
    if trad_match:
        spell_data['traditions'] = [clean_value(t).lower() for t in trad_match.group(1).split(',')]
        if trad_match.end() > end_of_mechanics: end_of_mechanics = trad_match.end()
    else:
        spell_data['traditions'] = []

    # 6. Traits
    search_area = content[name_match.end():end_of_mechanics] if name_match else content[:end_of_mechanics]
    traits_line_match = re.search(r'\n\s*([A-ZÀ-Ÿ\s]{10,})\s*\n', search_area)
    spell_data['traits'] = parse_traits(traits_line_match.group(1)) if traits_line_match else []

    if rank_match and rank_match.end() > end_of_mechanics:
        end_of_mechanics = rank_match.end()

    # 7. Sauvegardes
    save_patterns = {
        'criticalSuccess': r'\**Succès critique\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Succès|Échec|Intensifié)|$)',
        'success': r'\**Succès\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Succès|Échec|Intensifié)|$)',
        'failure': r'\**Échec\.\s?\**[\s]*(.*?)(?=\n\s*\**(?:Échec|Intensifié)|$)',
        'criticalFailure': r'\**Échec critique\.?\s?\**[\s]*(.*?)(?=\n\s*\**(?:Intensifié)|$)'
    }
    for key, pattern in save_patterns.items():
        m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if m: spell_data['savingThrows'][key] = clean_text(m.group(1))

    # 8. Intensification
    h_pattern = r'\**Intensifiés?\s*\((.*?)\)\.?\**\s*(.*?)(?=(?:\n\s*\**Intensifié)|$)'
    for m in re.finditer(h_pattern, content, re.DOTALL | re.IGNORECASE):
        type_val = re.sub(r'[\*]', '', m.group(1)).strip()
        spell_data['heightened'].append({
            "type": type_val,
            "text": clean_text(m.group(2))
        })

    # 9. Description (Soustraction propre)
    desc_raw = content[end_of_mechanics:]
    removal_patterns = [
        r'\**Succès critique\.?\s?\**[\s]*.*?(?=\n\s*\**(?:Succès|Échec|Intensifié)|$)',
        r'\**Succès\.\s?\**[\s]*.*?(?=\n\s*\**(?:Échec|Intensifié)|$)',
        r'\**Échec\.\s?\**[\s]*.*?(?=\n\s*\**(?:Échec|Intensifié)|$)',
        r'\**Échec critique\.?\s?\**[\s]*.*?(?=\n\s*\**(?:Intensifié)|$)',
        r'\**Intensifiés?\s*\((.*?)\)\.?\**\s*(.*?)(?=(?:\n\s*\**Intensifié)|$)'
    ]
    for p in removal_patterns:
        desc_raw = re.sub(p, '', desc_raw, flags=re.DOTALL | re.IGNORECASE)
        
    spell_data['description'] = clean_text(desc_raw)

    return spell_data

# ==========================================
# GESTION DU FLUX COMPLET
# ==========================================

def process_full_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Nettoyage et astuce pour toujours capturer le premier sort
    full_content = '\n' + clean_pdf_artifacts(full_content).strip()

    # Le split qui change tout : Lookahead sur un nom en majuscules suivi plus tard par SORT X
    split_pattern = re.compile(r'\n(?=\s*\**[A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-\'’]+\s*?\**\s*\n(?:.{1,400}?)\bSORT\s+\d+)', re.DOTALL)
    spell_blocks = split_pattern.split(full_content)
    
    spell_blocks = [b for b in spell_blocks if "SORT" in b]

    print(f"[MAIN] {len(spell_blocks)} sorts isolés et parés au traitement.")

    root = etree.Element("spells")
    for block in spell_blocks:
        data = parse_spell_block(block)
        print(f"  -> Traitement de : {data['name']}")
        
        s_el = etree.SubElement(root, "spell")
        etree.SubElement(s_el, "name").text = data['name']
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
        
        etree.SubElement(s_el, "description").text = data['description']

        if data['savingThrows']:
            st_el = etree.SubElement(s_el, "savingThrow")
            for k in ['criticalSuccess', 'success', 'failure', 'criticalFailure']:
                if k in data['savingThrows']:
                    etree.SubElement(st_el, k).text = data['savingThrows'][k]

        if data['heightened']:
            hl_el = etree.SubElement(s_el, "heightenList")
            for h in data['heightened']:
                el = etree.SubElement(hl_el, "heighten", type=h['type'])
                el.text = h['text']

    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"[MAIN] C'est dans la boîte : {output_path}")

if __name__ == "__main__":
    #process_full_file("./output/subset_1/sorts_MD.md", "data/spells/all_spells.xml", "xslt/spell.xsd")
    process_full_file("./output/subset_1/sorts_MD.md", "data/spells/all_spells.xml")