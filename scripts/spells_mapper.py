import re
import os
import sys
import time
from lxml import etree

from xml_validator import validate_xml
from slug_generator import generate_slug
from utils import strip_metadata, split_bullet_list, parse_table_markers

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
    content = strip_metadata(content)
    # 1. Gestion des retours à la ligne litéraux
    content = content.replace('\\n', '\n')
    
    # Cat E : Callout box _** (intro de chapitre, italic+bold non fermé)
    # Doit tourner AVANT la suppression des [[PAGE N]] car [[PAGE N]] sert de borne d'arrêt
    content = re.sub(r'\n\s*_\*\*[^\n]+(?:\n(?!\s*\[\[)[^\n]*)*', '', content)

    # 2. Purge des en-têtes/pieds de page et filigranes
    content = re.sub(r'\[\[PAGE \d+\]\]', '', content)
    content = re.sub(r'(?m)^\s*Sorts\s*$', '', content, flags=re.IGNORECASE)
    content = re.sub(r'(?m)^\s*# FLUX PRINCIPAL \(STATS\/BASE\)\s*$(?:\n\s*Livre des Joueurs)?\n*\*{0,2}\s*\d{1,3}\s?\d{0,3}\*{0,2}', '', content)
    # Suppression des légendes d'illustration + crédit artiste (légende indentée suivie d'une ligne email)
    content = re.sub(
        r'(?m)^[ \t]{3,}[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][a-zà-ÿ][^\n]{0,45}\n[ \t]*[^\n]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\n]*$\n?',
        '', content
    )
    content = re.sub(r'(?m)^.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}.*$\n?', '', content)
    # Cat A : Running heads — **NOM NOM** seul sur une ligne (nom répété deux fois = filigrane PDF)
    content = re.sub(r'(?m)^\s*\*\*([A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ\s]+?) \1\*\*\s*$', '', content)

    # 3. Suppression intelligente des sommaires (barres latérales)
    lines = content.split('\n')
    cleaned_lines = []
    streak = []
    empty_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        if len(stripped) == 0:
            empty_count += 1
            streak.append(line)
            # Sécurité 1 : Deux lignes vides consécutives brisent la série
            if empty_count >= 2:
                if len([l for l in streak if l.strip()]) >= 5:
                    pass # On jette le sommaire
                else:
                    cleaned_lines.extend(streak)
                streak = []
        else:
            empty_count = 0
            is_short = len(stripped) < 30
            is_title = re.search(r'\b(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d+', stripped)
            # Sécurité 2 : Un point final signifie que c'est une vraie phrase
            ends_with_dot = stripped.endswith('.')
            
            if is_short and not is_title and not ends_with_dot:
                streak.append(line)
            else:
                # C'est une ligne longue, un titre, ou une fin de phrase => on casse la série
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
    """Nettoie le texte PDF : retire les coupures de mots (tiret + espace) et normalise les espaces."""
    if not text: return ""
    text = re.sub(r'[\u002D\u2011]\n?\s+', '', text)  # tiret normal et tiret insécable (U+2011)
    text = re.sub(r'\*+', '', text)  # strip marqueurs markdown gras/italique résiduels
    return re.sub(r'\s+', ' ', text).strip()

def clean_desc(text):
    """Nettoie une description : corrige les coupures de mots, préserve le gras (**), normalise les espaces."""
    if not text: return ""
    text = re.sub(r'[\u002D\u2011]\n?\s+', '', text)  # coupures de mots (tiret normal + insécable U+2011)
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
    """Génère un nœud XML en convertissant les _mot_ en balises <spellRef>. Retourne le nœud créé."""
    if tag_name is None:
        el = parent
    else:
        el = etree.SubElement(parent, tag_name)

    if not text_content:
        return el

    parts = re.split(r'_([^_]+?)_', text_content)
    el.text = parts[0]
    for i in range(1, len(parts), 2):
        spell_el = etree.SubElement(el, "spellRef")
        spell_el.text = parts[i]
        if i + 1 < len(parts):
            spell_el.tail = parts[i+1]
    return el

# ==========================================
# PARSING D'UN BLOC DE SORT
# ==========================================

def parse_spell_block(content):
    spell_data = {'savingThrows': {}, 'heightened': [], 'tables': []}
    
    # **NOUVEAU** : Détecter et couper au chapitre suivant
    # Les chapitres commencent par des titres en majuscules seuls sur une ligne
    # ou par "[[PAGE X]]" suivi d'un titre de chapitre
    chapter_markers = [
        # Coupe uniquement sur une ligne all-caps qui n'est PAS suivie de mécaniques
        # (Tradition, **Portée, **Cible…) : les lignes de traits sont toujours suivies de mécaniques
        rf'(?m)^[{UPPER}][\s{UPPER}]{{2,}}$(?![\s\S]{{0,200}}?(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d{{1,2}})(?![\s\S]{{0,250}}?\n\s*(?:[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][a-zà-ÿ]|\*\*(?:Portée|Cibles?|Défense|Durée|Zone|Incantation|Déclencheur)))',
        rf'(?m)^\s{{0,30}}\*\*[{UPPER}][{UPPER}\s]{{4,}}',  # Cat C : **SIDEBAR TITRE** à faible indent
    ]

    # Trouver la fin de l'en-tête du sort (rang) pour ne pas couper avant
    rank_end = 0
    rank_hdr = re.search(r'\b(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d+', content)
    if rank_hdr:
        rank_end = rank_hdr.end()

    for marker in chapter_markers:
        m = re.search(marker, content)
        if m and m.start() > rank_end:
            content = content[:m.start()]
            break

    
    # Nettoyage
    content = '\n' + clean_pdf_artifacts(content).strip()

    # 0. Extraction anticipée des markers de tableaux (avant tout parsing regex)
    content, spell_data['tables'] = parse_table_markers(content)

# 1. En-tête (Nom) - Utilise la nouvelle constante UPPER
    name_regex = rf'^\s*\**([{UPPER}][{UPPER}\s\-‑\'’]+)(?:(?:\*{{2}}(?:\s|$))|(?:SORT|TOUR DE MAGIE|FOCALISÉ))'
    name_match = re.search(name_regex, content, re.MULTILINE)
    spell_data['name'] = clean_text(name_match.group(1)) if name_match else "INCONNU"

    # 2. Rang (Gère Sort et Tour de Magie)
    rank_match = re.search(r'\b(SORT|TOUR DE MAGIE|FOCALISÉ)\s+(\d+)', content)
    spell_data['type'] = rank_match.group(1) if rank_match else "SORT"
    spell_data['rank'] = rank_match.group(2) if rank_match else "1"

    # 3. Actions (Isolé entre le Nom et le Rang)
    header_end = rank_match.start() if rank_match else 200
    header_area = content[:header_end]
    # Détection des actions variables "N À M" (ex: 1 À 3, 2 À 3) — Cat B les a normalisées en une ligne
    range_match = re.search(r'\b([123])\s+[Àà]\s+([123])\b', header_area)
    if range_match:
        spell_data['actions'] = f"{range_match.group(1)}-{range_match.group(2)}"
    else:
        action_match = re.search(r'(?m)^\s*\**\s*([0123R])\s*\**\s*$', header_area)
        if not action_match:
            action_match = re.search(r'\b(0|1|2|3|R)\b', header_area[name_match.end() if name_match else 0:])
        spell_data['actions'] = action_match.group(1) if action_match else None
    # Réactions sans chiffre d'action : détecter via **Déclencheur** comme label de mécanique
    # (pas case-insensitive pour éviter "un déclencheur spécifique" dans les descriptions)
    if not spell_data['actions'] and re.search(r'(?:^|\n)\s*\*{1,2}Déclencheur[.*]?\*{0,2}\s', content):
        spell_data['actions'] = 'R'

    # 4. Mécaniques stricto sensu (Bloque au premier saut de ligne ou point-virgule)
    mech_prefix = r'(?:(?<=\n)|(?<=;)|(?<=^))\s*\**\s*'  # \s* final tolère un espace entre ** et le nom du champ
    mechanics = {
        'range': mech_prefix + r'Portée\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'targets': mech_prefix + r'[Cc]ibles?\**[\s:]*(.*?)(?=\s*(?:;|\n\s*\*\*|\n\s*[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ]|$))',
        'defense': mech_prefix + r'Défense\**[\s:]*(.*?)(?=\*{0,2}\s*(?:;|\n|$))',
        'duration': mech_prefix + r'Durée\*+[\s:]*(.*?)(?=\s*(?:;|\n|$))',  # \*+ évite de matcher "Durée maximale" dans les textes de sauvegarde
        'area': mech_prefix + r'Zone[\s:]*\**[\s:]*(.*?)(?=\s*(?:;|\n\s*[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ]|$|\*\*))',
        'cast': mech_prefix + r'Incantation\**[\s:]*(.*?)(?=\s*(?:;|\n|$))',
        'trigger': mech_prefix + r'Déclencheur[.*]?\**[\s:]*(.*?)(?=\s*(?:;|\n\s*\*\*|\n\s*[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ]|$))',
    }
    
    mech_ends = []
    for key, pattern in mechanics.items():
        m = re.search(pattern, content, re.DOTALL)
        if m:
            spell_data[key] = clean_value(m.group(1))
            mech_ends.append(m.end())
        else:
            spell_data[key] = None

    # 5. Traditions
    trad_match = re.search(mech_prefix + r'Traditions?\s?\**[\s:]*([a-zA-Zà-ÿ,\s]+?)(?=\s*(?:;|\n|$))', content, re.IGNORECASE)
    VALID_TRADITIONS = {'arcanique', 'occulte', 'primordiale', 'divine'}
    if trad_match:
        parsed = [clean_value(t).lower() for t in trad_match.group(1).split(',')]
        spell_data['traditions'] = [t for t in parsed if t in VALID_TRADITIONS]
        mech_ends.append(trad_match.end())
    else:
        spell_data['traditions'] = []

    # 6. Traits (Entre le Rang et la première mécanique)
    # Détection de la première mécanique ou du début de description (Capital+minuscule)
    first_mech_start = min([m.start() for m in re.finditer(
        rf'(?:(?<=\n)|(?<=;))\s*\**(?:Portée|Cibles?|Défense|Durée|Zone|Incantation|Traditions?|Protecteur|Muse|Déclencheur|Conditions?|Leçon|[{UPPER}][a-zà-ÿ])',
        content)] or [len(content)])
    traits_area = content[rank_match.end() if rank_match else 200:first_mech_start]
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

    # 8. Intensification — formes avec type explicite : "(Xe)" ou "(+M)"
    h_pattern = r'(?:^|\n)\s*\**Intensifiés?\s*\((.*?)\)\.?\s*\**\s*(.*?)(?=(?:\n\s*\**Intensifié)|$)'
    for m in re.finditer(h_pattern, content, re.DOTALL | re.IGNORECASE):
        type_val = re.sub(r'[\*]', '', m.group(1)).strip()
        spell_data['heightened'].append({
            "type": type_val,
            "text": clean_text(m.group(2))
        })
    # Cas particulier : "Intensifié. Comme indiqué sous le trait convocation"
    # → expansion en table fixe rang/niveau (règle du trait convocation, identique pour tous les sorts de convocation)
    CONVOCATION_HEIGHTEN = [
        ("2e", "Niveau 1."), ("3e", "Niveau 2."), ("4e", "Niveau 3."),
        ("5e", "Niveau 5."), ("6e", "Niveau 7."), ("7e", "Niveau 9."),
        ("8e", "Niveau 11."), ("9e", "Niveau 13."), ("10e", "Niveau 15."),
    ]
    if re.search(r'(?:^|\n)\s*\**Intensifiés?\.\s*\**\s*Comme indiqué sous le trait convocation', content, re.IGNORECASE):
        spell_data['heightened'].extend({"type": t, "text": v} for t, v in CONVOCATION_HEIGHTEN)
    # Correction d'erreur PDF connue : BARRAGE DE FORCE a "Intensifié (2e)" au lieu de "(+2)"
    if spell_data.get('name') == 'BARRAGE DE FORCE':
        for h in spell_data['heightened']:
            if h['type'] == '2e':
                h['type'] = '+2'

    # 9. Description (Démarre après la dernière mécanique, s'arrête avant la première sauvegarde)
    desc_start = max(mech_ends) if mech_ends else header_end
    
    save_starts = []
    for p in save_patterns.values():
        m = re.search(p, content, re.DOTALL | re.IGNORECASE)
        if m: save_starts.append(m.start())
    for m in re.finditer(h_pattern, content, re.DOTALL | re.IGNORECASE):
        save_starts.append(m.start())
        
    desc_end = min(save_starts) if save_starts else len(content)
    intro_raw, items_raw = split_bullet_list(content[desc_start:desc_end])
    spell_data['description'] = clean_desc(intro_raw)
    spell_data['list_items'] = [clean_desc(item) for item in items_raw]

    return spell_data

# ==========================================
# PARSING COMPLET DES SORTS
# ==========================================

def parse_spells_md(content):
    """Extrait et parse tous les sorts du Markdown brut."""
    spells_data = []
    print("[PARSING] Début de l'analyse des sorts...")


    # Cat B : Normaliser les headers multi-lignes "1 ** À** 3 **" en une seule ligne
    # pour que split_regex puisse les détecter dans la fenêtre de 150 chars
    content = re.sub(
        r'(\*\*\s*\n\s*)([123])\s*\n\s*\**\s*(À)\**\s*\n\s*([123])\s*\n\s*(\**)',
        r'\1\2 \3 \4 \5',
        content
    )

    # Cat F : Nom de sort sur deux lignes — "**NOM\nSUITE**" → "**NOM SUITE**"
    # Ex: "**CONVOCATION DE PLANTE\nOU DE CHAMPIGNON**"
    content = re.sub(
        rf'\*\*([{UPPER}][{UPPER}\s\-‑\']+)\n([{UPPER}][{UPPER}\s\-‑\']*)\*\*',
        r'**\1 \2**',
        content
    )

    # Découpage robuste avec la constante UPPER pour éviter de couper sur un "é"
    split_regex = rf'\n(?=\s*\**[{UPPER}][{UPPER}\s\-‑\'’]+\s?\**\s*(?:.{{0,150}}?)\b(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d+)'
    split_pattern = re.compile(split_regex, re.DOTALL)
    spell_blocks = split_pattern.split(content)
    
    spell_blocks = [b for b in spell_blocks if re.search(r'\b(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d+', b)]

    print(f"[PARSING] {len(spell_blocks)} sorts isolés.")

    for block in spell_blocks:
        if not re.search(r'\b(?:SORT|TOUR DE MAGIE|FOCALISÉ)\s+\d+', block):
            print(f"[PARSING]   ⚠ bloc sans rang ignoré: {block[:80].strip()!r}")
            continue
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
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../schema/spell.xsd")

    seen_ids: set = set()
    for data in spells_data:
        # Génération de l'ID dynamique (dédupliqué si nom INCONNU ou collision)
        base_id = generate_slug("spell", data['name'])
        trait_id = base_id
        if trait_id in seen_ids:
            counter = 2
            while f"{base_id}-{counter}" in seen_ids:
                counter += 1
            trait_id = f"{base_id}-{counter}"
        seen_ids.add(trait_id)
        s_el = etree.SubElement(root, "spell", id=trait_id)

        etree.SubElement(s_el, "name").text = data['name']

        if data['type']: 
            s_el.set('type',"spell" if data['type']=="SORT" else "cantrip" if data['type']=="TOUR DE MAGIE" else "focus" if data['type']=="FOCALISÉ" else "unknown")
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

        for field in ['cast', 'trigger', 'range', 'area', 'targets', 'defense', 'duration']:
            if data.get(field): etree.SubElement(s_el, field).text = data[field]
        
        # description est requise par le XSD — on la crée même si vide
        desc_node = add_rich_text(s_el, data.get('description'), "description")
        if data.get('list_items'):
            list_node = etree.SubElement(desc_node, "list")
            for item in data['list_items']:
                etree.SubElement(list_node, "listItem").text = item

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

        for tbl in data.get('tables', []):
            tbl_el = etree.SubElement(s_el, "table")
            if tbl.get('header'):
                hdr_el = etree.SubElement(tbl_el, "headerLine")
                for c in tbl['header']:
                    etree.SubElement(hdr_el, "cell").text = c
            for row in tbl.get('rows', []):
                row_el = etree.SubElement(tbl_el, "line")
                for c in row:
                    etree.SubElement(row_el, "cell").text = c

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
    
    total_time = time.time() - start_time
    print(f"[XML] ✓ Fichier sauvegardé à {output_path} - {total_time:.3f}s")

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    #input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/subset_1/sorts_MD.md"
    #output_file = sys.argv[2] if len(sys.argv) > 2 else "./data/spells/all_spells.xml"
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/regen_sorts/test_sorts.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./output/regen_sorts/sorts_ldj2.xml"

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

        xsd_file = "./schema/spell.xsd"
        if os.path.exists(output_file) and os.path.exists(xsd_file):
            validate_xml(output_file, xsd_file)
        else:
            print(f"[WARNING] Fichier XSD introuvable ({xsd_file}), validation ignorée.")
    else:
        print(f"[MAIN] ✗ Erreur : le fichier {input_file} n'existe pas.")

    total_elapsed = time.time() - start_total
    print(f"\n[MAIN] Temps total de traitement: {total_elapsed:.3f}s")
    print("="*60)