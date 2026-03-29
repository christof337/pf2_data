import re
import os
import sys
import time
from lxml import etree

# ==========================================
# UTILITAIRES DE TEXTE
# ==========================================

def clean_text(text):
    """Nettoie les sauts de ligne et espaces superflus."""
    if not text: return ""
    # Recolle les mots coupés par un tiret en fin de ligne (spécificité PDF)
    text = text.replace("-\n", "").replace("- ", "")
    return re.sub(r'\s+', ' ', text).strip()

# ==========================================
# PARSING SPÉCIFIQUE SORTS
# ==========================================

def parse_traits(traits_raw):
    # 1. Liste des traits "composés" connus
    multi_word_traits = [
        "NON LÉTAL", 
        "PEU COURANT", 
        "MISE HORS DE COMBAT"
    ]
    
    # On normalise (MAJUSCULES et nettoyage espaces)
    text = traits_raw.upper().strip()
    
    final_traits = []
    
    # 2. On extrait d'abord les traits composés pour ne pas qu'ils soient splittés
    for multi in multi_word_traits:
        if multi in text:
            final_traits.append(multi)
            text = text.replace(multi, "") # On le retire pour ne pas le re-traiter
            
    # 3. On split le reste par les espaces classiques
    remaining = text.split()
    for t in remaining:
        if len(t) > 1: # Évite les résidus de ponctuation
            final_traits.append(t.strip())
            
    return final_traits

def parse_spell_md(content):
    """Extrait les données d'un sort depuis le Markdown."""
    spell_data = {}
    print("[PARSING] Début de l'analyse du sort...")

    # 1. Nom et Rang (ex: **AGITATION ** ... SORT 1)
    name_match = re.search(r'\*\*([A-ZÀ-Ÿ\s\-]+?)\s*\*\*', content)
    rank_match = re.search(r'SORT\s+(\d+)', content)
    
    spell_data['name'] = name_match.group(1).strip() if name_match else "NOM INCONNU"
    spell_data['rank'] = rank_match.group(1) if rank_match else "1"

    # 2. Actions (souvent un chiffre isolé juste avant ou après le nom)
    # On cherche un chiffre 1, 2 ou 3 entouré d'espaces ou retours chariots
    action_match = re.search(r'(?:\n|^)\s*([123])\s*(?:\n)', content)
    spell_data['actions'] = action_match.group(1) if action_match else None

    # 3. Traits (Ligne juste après le Rang, souvent en MAJUSCULES)
    # On cherche les mots en majuscules avant "Traditions"
    traits_match = re.search(r'SORT \d+\s+([A-ZÀ-Ÿ\s]+?)\n', content)
    if traits_match:
        traits_raw = parse_traits(traits_match.group(1).strip())
        spell_data['traits'] = traits_raw

    # 4. Traditions
    trad_match = re.search(r'Traditions\*\* (.*?)(?:\n|$)', content)
    if trad_match:
        spell_data['traditions'] = [t.strip().lower() for t in trad_match.group(1).split(',')]

    # 5. Mécaniques (Portée, Cible, Défense, Durée)
    spell_data['range'] = re.search(r'\*\*Portée\*\* ([^;|\n]+)', content)
    spell_data['range'] = spell_data['range'].group(1).strip() if spell_data['range'] else None
    
    spell_data['targets'] = re.search(r'\*\*Cible\*\* ([^;|\n]+)', content)
    spell_data['targets'] = spell_data['targets'].group(1).strip() if spell_data['targets'] else None
    
    spell_data['defense'] = re.search(r'\*\*Défense\*\* ([^;|\n]+)', content)
    spell_data['defense'] = spell_data['defense'].group(1).strip() if spell_data['defense'] else None
    
    spell_data['duration'] = re.search(r'\*\*Durée\*\* ([^;|\n]+)', content)
    spell_data['duration'] = spell_data['duration'].group(1).strip() if spell_data['duration'] else None

    # 6. Blocs de résultats (Sauvegardes)
    save_blocks = {
        'criticalSuccess': r'\*\*Succès critique\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'success': r'\*\*Succès\.\s?\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'failure': r'\*\*Échec\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'criticalFailure': r'\*\*Échec critique\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)'
    }
    spell_data['savingThrows'] = {}
    for key, pattern in save_blocks.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            spell_data['savingThrows'][key] = clean_text(match.group(1))

    # 7. Intensification (Heightened)
    # Cherche "Intensifié (+1)" ou "Intensifiés (+1)" ou "Intensifié (4e)"
    heighten_pattern = r'\*\*Intensifiés?\s+\((.*?)\)\.\*\*\s*(.*?)(?=\s*\*\*|$)'
    heighten_matches = re.findall(heighten_pattern, content, re.DOTALL)
    spell_data['heightened'] = [{"type": h[0], "text": clean_text(h[1])} for h in heighten_matches]

    # 8. Description (le texte restant)
    # On prend ce qui suit la durée et qui précède les blocs de succès/intensification
    desc_start = content.find(spell_data['duration']) + len(spell_data['duration']) if spell_data['duration'] else 0
    if not desc_start:
         desc_start = content.find("Traditions") # Fallback
    
    # On cherche la première occurrence d'un bloc spécial pour arrêter la description
    first_block = 999999
    for pattern in list(save_blocks.values()) + [r'\*\*Intensifié']:
        m = re.search(pattern, content)
        if m and m.start() < first_block:
            first_block = m.start()
    
    spell_data['description'] = clean_text(content[desc_start:first_block])

    return spell_data

# ==========================================
# GÉNÉRATION XML
# ==========================================

def generate_spell_xml(data, output_path):
    """Génère le fichier XML à partir des données extraites."""
    root = etree.Element("spells")
    spell = etree.SubElement(root, "spell")

    etree.SubElement(spell, "name").text = data['name']
    etree.SubElement(spell, "rank").text = data['rank']
    if data['actions']: etree.SubElement(spell, "actions").text = data['actions']

    if 'traits' in data:
        traits_el = etree.SubElement(spell, "traits")
        for t in data['traits']:
            etree.SubElement(traits_el, "trait").text = t

    if 'traditions' in data:
        trad_el = etree.SubElement(spell, "traditions")
        for tr in data['traditions']:
            etree.SubElement(trad_el, "tradition").text = tr

    if data['range']: etree.SubElement(spell, "range").text = data['range']
    if data['targets']: etree.SubElement(spell, "targets").text = data['targets']
    if data['defense']: etree.SubElement(spell, "defense").text = data['defense']
    if data['duration']: etree.SubElement(spell, "duration").text = data['duration']
    
    etree.SubElement(spell, "description").text = data['description']

    if data['savingThrows']:
        st_el = etree.SubElement(spell, "savingThrow")
        for key, value in data['savingThrows'].items():
            etree.SubElement(st_el, key).text = value

    if data['heightened']:
        h_list = etree.SubElement(spell, "heightenList")
        for h in data['heightened']:
            el = etree.SubElement(h_list, "heighten", type=h['type'])
            el.text = h['text']

    # Sauvegarde
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

# ==========================================
# VALIDATION XSD
# ==========================================

def validate_xml(xml_path, xsd_path):
    try:
        schema_root = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_root)
        xml_doc = etree.parse(xml_path)
        if schema.validate(xml_doc):
            print(f"[VALIDATION] ✓ Le fichier XML est conforme au XSD.")
            return True
        else:
            print(f"[VALIDATION] ❌ INVALIDE !")
            for error in schema.error_log:
                print(f"    - Ligne {error.line}: {error.message}")
            return False
    except Exception as e:
        print(f"[VALIDATION] Erreur : {e}")
        return False

# ==========================================
# EXECUTION
# ==========================================

if __name__ == "__main__":
    input_file = "./output/subset_1/agitation.md"
    output_file = "./data/spells/agitation.xml"
    xsd_file = "./xslt/spell.xsd"

    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = parse_spell_md(content)
        generate_spell_xml(data, output_file)
        
        print(f"[MAIN] ✓ XML généré : {output_file}")
        
        if os.path.exists(xsd_file):
            validate_xml(output_file, xsd_file)