import re
import os
from lxml import etree

def parse_monster_text(content):
    """Analyse le texte brut pour extraire les données PF2e"""
    monster_data = {}
    
    # 1. Extraction du Nom et du Niveau
    # Le nom est souvent en MAJUSCULES juste avant "CRÉATURE"
    name_match = re.search(r'([A-ZÀ-Ÿ\s\-]+)\n(?:.*?)CRÉATURE\s+(\d+)', content)
    if name_match:
        monster_data['name'] = name_match.group(1).strip()
        monster_data['level'] = name_match.group(2)

    # 2. Caractéristiques (For, Dex, etc.)
    # Format type : For +6, Dex +3, Con +4...
    attr_pattern = r'(For|Dex|Con|Int|Sag|Cha)\s+([\+\-]\d+)'
    attrs = re.findall(attr_pattern, content)
    monster_data['attributes'] = {k: v for k, v in attrs}

    # 3. Défense (CA et PV)
    ca_match = re.search(r'CA\s+(\d+)', content)
    if ca_match: monster_data['ac'] = ca_match.group(1)
    
    pv_match = re.search(r'PV\s+(\d+)', content)
    if pv_match: monster_data['hp'] = pv_match.group(1)

    # 4. Actions de combat (Détection simplifiée par les chiffres d'action)
    # Cherche les lignes commençant par un nom suivi de [1], [2] ou [3]
    # Ou simplement des motifs comme "Corps à corps"
    melee_pattern = r'Corps à corps\s+(.*?)\s+([\+\-]\d+).*?Dégâts\s+(.*)'
    melees = re.findall(melee_pattern, content)
    monster_data['attacks'] = melees

    return monster_data

def generate_xml(data, lore_text, output_path):
    """Construit le fichier XML selon la structure Source of Truth"""
    root = etree.Element("monster", source="EditeurOfficiel")
    
    # Identification
    id_node = etree.SubElement(root, "identity")
    etree.SubElement(id_node, "name").text = data.get('name', 'Inconnu')
    etree.SubElement(id_node, "level").text = data.get('level', '0')

    # Statistiques
    stats_node = etree.SubElement(root, "statistics")
    etree.SubElement(stats_node, "ac").text = data.get('ac', '0')
    etree.SubElement(stats_node, "hp").text = data.get('hp', '0')
    
    attr_node = etree.SubElement(stats_node, "attributes")
    for code, val in data.get('attributes', {}).items():
        etree.SubElement(attr_node, code.lower()).text = val

    # Lore (issu de votre encart détecté à l'étape 1)
    if lore_text:
        lore_node = etree.SubElement(root, "lore")
        lore_node.text = etree.CDATA(lore_text.strip())

    # Sauvegarde
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

def process_structured_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # On sépare le flux principal du lore (via vos marqueurs de l'étape 1)
    parts = full_content.split("# ENCARTS DETECTÉS (LORE/ANNEXES)")
    main_flow = parts
    lore_flow = parts[1] if len(parts) > 1 else ""

    #data = parse_monster_text(main_flow)
    data = parse_monster_text(full_content)
    
    output_xml = f"./data/monsters/{data.get('name', 'test').replace(' ', '_')}.xml"
    generate_xml(data, lore_flow, output_xml)
    print(f"XML généré : {output_xml}")

if __name__ == "__main__":
    process_structured_markdown("./output/subset_1/page_1_structured.md")