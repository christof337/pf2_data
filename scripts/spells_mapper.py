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
# UTILITAIRES
# ==========================================

def clean_text(text):
    if not text: return ""
    # Recolle les mots coupés par un tiret en fin de ligne
    text = text.replace("-\n", "").replace("- ", "")
    return re.sub(r'\s+', ' ', text).strip()

def parse_traits(traits_raw):
    """Gère les traits simples et les traits multi-mots (ex: NON LÉTAL)."""
    text = traits_raw.upper().strip()
    final_traits = []
    
    # Extraction des traits composés d'abord
    for multi in MULTI_WORD_TRAITS:
        if multi in text:
            final_traits.append(multi)
            text = text.replace(multi, "")
            
    # Split du reste par espace
    remaining = text.split()
    for t in remaining:
        if len(t) > 2: # Évite les débris de ponctuation
            final_traits.append(t.strip())
            
    return final_traits

# ==========================================
# PARSING D'UN BLOC DE SORT
# ==========================================

def parse_spell_block(content):
    """Analyse un bloc de texte correspondant à UN SEUL sort."""
    spell_data = {}
    
    # 1. Nom (souvent la première ligne en gras)
    name_match = re.search(r'\*\*([A-ZÀ-Ÿ\s\-]{3,})\s*\*\*', content)
    spell_data['name'] = name_match.group(1).strip() if name_match else "INCONNU"

    # 2. Rang (SORT X)
    rank_match = re.search(r'SORT\s+(\d+)', content)
    spell_data['rank'] = rank_match.group(1) if rank_match else "1"

    # 3. Actions (Chiffre isolé 1, 2 ou 3)
    action_match = re.search(r'(?:\n|^)\s*([123])\s*(?:\n)', content)
    spell_data['actions'] = action_match.group(1) if action_match else None

    # 4. Traits (Zone entre le Rang et les Traditions)
    # On cherche les mots en MAJUSCULES
    traits_section = re.search(r'SORT \d+\s+([A-ZÀ-Ÿ\s]+?)\n\s*Traditions', content, re.DOTALL)
    if traits_section:
        spell_data['traits'] = parse_traits(traits_section.group(1))
    else:
        # Fallback si Traditions n'est pas juste après
        spell_data['traits'] = []

    # 5. Traditions
    trad_match = re.search(r'Traditions\*\* (.*?)(?:\n|$)', content)
    if trad_match:
        spell_data['traditions'] = [t.strip().lower() for t in trad_match.group(1).split(',')]

    # 6. Mécaniques
    fields = {
        'range': r'\*\*Portée\*\* ([^;|\n]+)',
        'targets': r'\*\*Cible\*\* ([^;|\n]+)',
        'defense': r'\*\*Défense\*\* ([^;|\n]+)',
        'duration': r'\*\*Durée\*\* ([^;|\n]+)'
    }
    for key, pattern in fields.items():
        match = re.search(pattern, content)
        spell_data[key] = match.group(1).strip() if match else None

    # 7. Sauvegardes / Succès
    save_patterns = {
        'criticalSuccess': r'\*\*Succès critique\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'success': r'\*\*Succès\s?\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'failure': r'\*\*Échec\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)',
        'criticalFailure': r'\*\*Échec critique\.\*\*\s*(.*?)(?=\s*\*\*|\s*Intensifié|$)'
    }
    spell_data['savingThrows'] = {}
    for key, pattern in save_patterns.items():
        m = re.search(pattern, content, re.DOTALL)
        if m: spell_data['savingThrows'][key] = clean_text(m.group(1))

    # 8. Intensification
    h_pattern = r'\*\*Intensifiés?\s+\((.*?)\)\.\*\*\s*(.*?)(?=\s*\*\*|$)'
    h_matches = re.findall(h_pattern, content, re.DOTALL)
    spell_data['heightened'] = [{"type": h[0], "text": clean_text(h[1])} for h in h_matches]

    # 9. Description (nettoyage grossier des blocs déjà extraits)
    # On prend ce qui suit la Durée (ou Traditions) et précède les Succès/Intensifié
    start_anchor = spell_data['duration'] if spell_data['duration'] else "Traditions"
    start_pos = content.find(start_anchor) + len(start_anchor)
    
    # On cherche le début du premier bloc de réussite ou d'intensification
    end_pos = len(content)
    for p in list(save_patterns.values()) + [r'\*\*Intensifié']:
        m = re.search(p, content)
        if m and m.start() < end_pos:
            end_pos = m.start()
    
    spell_data['description'] = clean_text(content[start_pos:end_pos])

    return spell_data

# ==========================================
# GESTION DU FLUX COMPLET
# ==========================================

def process_full_file(input_path, output_path, xsd_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # DÉCOUPAGE : On cherche les titres de sorts (**NOM**) 
    # suivis d'un indicateur de rang (SORT X)
    spell_blocks = re.split(r'\n(?=\s*\*\*[^a-z]+\*\*\s*\n?\s*\d*\s*\n?\s*\*\*?\s*SORT)', full_content)
    
    # Nettoyage pour ignorer l'en-tête du fichier MD
    spell_blocks = [b for b in spell_blocks if "SORT" in b]

    print(f"[MAIN] {len(spell_blocks)} sorts détectés.")

    root = etree.Element("spells")
    for block in spell_blocks:
        data = parse_spell_block(block)
        print(f"  -> Traitement de : {data['name']}")
        
        # Construction XML (identique au précédent)
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

        for field in ['range', 'targets', 'defense', 'duration']:
            if data[field]: etree.SubElement(s_el, field).text = data[field]
        
        etree.SubElement(s_el, "description").text = data['description']

        if data['savingThrows']:
            st_el = etree.SubElement(s_el, "savingThrow")
            for k, v in data['savingThrows'].items():
                etree.SubElement(st_el, k).text = v

        if data['heightened']:
            hl_el = etree.SubElement(s_el, "heightenList")
            for h in data['heightened']:
                el = etree.SubElement(hl_el, "heighten", type=h['type'])
                el.text = h['text']

    # Sauvegarde finale
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"[MAIN] XML généré : {output_path}")

if __name__ == "__main__":
    process_full_file("./output/subset_1/sorts_MD.md", "data/spells/all_spells.xml", "xslt/spell.xsd")