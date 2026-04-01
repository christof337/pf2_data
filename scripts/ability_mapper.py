"""
ability_mapper.py
Parsing du Glossaire des pouvoirs (Capacités universelles) du Livre des Monstres PF2e.
Entrée  : fichier MD extrait par extract_pdf.py (output/ldm_full/...)
Sortie  : data/abilities/abilities.xml
"""

import re
import os
import sys
from lxml import etree

# Ajout du répertoire scripts au path pour les imports locaux
sys.path.insert(0, os.path.dirname(__file__))
from slug_generator import generate_slug


# ==========================================
# UTILITAIRES
# ==========================================

def clean_text(text):
    """Normalise les espaces et sauts de ligne."""
    # Remplace les puces de substitution '°' ou '°' par rien
    text = re.sub(r'[°\ufffd]', '', text)
    # Normalise les espaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Réduit les sauts de ligne multiples à un seul
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_glossary_section(md_content):
    """
    Extrait la section 'GLOSSAIRE DES POUVOIRS' du fichier MD complet.
    Retourne le texte brut de la section.
    """
    # Début : marqueur du glossaire
    start_match = re.search(r'GLOSSAIRE\s+DES\s+POUVOIRS', md_content)
    if not start_match:
        print("[ABILITY] Aucune section 'GLOSSAIRE DES POUVOIRS' trouvée.")
        return None

    # Fin : on s'arrête à la PAGE 364 (début des Rituels)
    # Note : "Rituels et types" apparaît dans les sidebars de navigation répétées,
    # on utilise donc le marqueur de page qui est plus fiable.
    end_markers = [
        r'\[\[PAGE\s+364\]\]',
        r'\[\[PAGE\s+36[5-9]\]\]',
        r'\[\[PAGE\s+3[7-9]\d\]\]',
    ]
    text_from_start = md_content[start_match.start():]

    end_pos = len(text_from_start)
    for marker in end_markers:
        m = re.search(marker, text_from_start)
        if m and m.start() < end_pos:
            end_pos = m.start()

    return text_from_start[:end_pos]


# ==========================================
# PARSING DES CAPACITÉS
# ==========================================

def parse_abilities_md(md_content):
    """
    Parse la section Glossaire des pouvoirs.
    Retourne une liste de dicts avec les champs :
      id, name, actions, traits, conditions, trigger, effect, description
    """
    print("[PARSING] Extraction de la section Glossaire des pouvoirs...")
    glossary_text = extract_glossary_section(md_content)
    if not glossary_text:
        return []

    # Suppression des artefacts de navigation (numéros de page, tags PAGE, headers)
    # Supprime les blocs [[PAGE N]] et les headers "# FLUX PRINCIPAL..."
    clean = re.sub(r'\[\[PAGE\s+\d+\]\]', '', glossary_text)
    clean = re.sub(r'#\s+FLUX PRINCIPAL.*?\n', '', clean)
    clean = re.sub(r'#\s+ENCARTS.*?\n', '', clean)
    # Retire les numéros de page isolés (ex: "359 359" ou "**360 360**")
    clean = re.sub(r'\*?\*?\d{3}\s+\d{3}\*?\*?', '', clean)
    # Retire les entêtes de navigation (Introduction / Monstres / Glossaire...)
    clean = re.sub(r'(Introduction|Monstres|Glossaire des\s+pouvoirs et traits|Rituels et types|Créatures par\s+niveau|Livre des Monstres|FRANCK PONT.*?\n)', '', clean)
    # Retire le titre du glossaire lui-même
    clean = re.sub(r'GLOSSAIRE\s+DES\s+POUVOIRS', '', clean)
    # Retire le texte d'introduction en italique (***...)
    clean = re.sub(r'\*{1,3}Vous trouverez.*?celui[‑\-]ci\.', '', clean, flags=re.DOTALL)
    # Remplace les points en caractère spécial par des points normaux
    clean = clean.replace('°', '.').replace('\ufffd', '.')

    # -------------------------------------------------------
    # Découpage en blocs individuels par capacité
    # On reconnaît une capacité par son titre en gras suivi
    # optionnellement d'un code d'actions (0, 1, 2, 3, 9, R)
    # -------------------------------------------------------
    # Pattern : ** ou * + NOM EN GRAS **
    # Le nom peut contenir des majuscules, minuscules, espaces, accents, tirets
    ability_pattern = re.compile(
        r'\*\*([A-ZÀ-Ÿa-zà-ÿ][A-ZÀ-Ÿa-zà-ÿ0-9°\s\'\-éàèêëîïôùûü]+?)\*\*',
        re.MULTILINE
    )

    all_matches = list(ability_pattern.finditer(clean))
    abilities = []

    for i, m in enumerate(all_matches):
        raw_name = m.group(1).strip().rstrip('.')

        # Ignorer les faux positifs : ne garder que les titres qui commencent
        # en début de ligne ou après des espaces d'indentation (début de ligne PDF)
        # On exclut les titres au milieu du texte (précédés par du texte non-blanc)
        pre_text = clean[max(0, m.start()-5):m.start()]
        if pre_text and not re.search(r'[\n]', pre_text) and pre_text.strip():
            continue

        # Délimitation : de la fin du titre jusqu'au début du suivant (ou fin)
        block_start = m.end()
        block_end = all_matches[i+1].start() if i+1 < len(all_matches) else len(clean)
        raw_body = clean[block_start:block_end]

        # --- Actions ---
        actions = None
        body = raw_body.strip()
        # Ligne avec juste un chiffre ou "R" (code actions)
        action_match = re.match(r'^\s*([0-3R9])\s*\n', body)
        if action_match:
            actions = action_match.group(1)
            body = body[action_match.end():].strip()
        else:
            # Actions inline après le titre : "1 Le monstre..."
            action_inline = re.match(r'^\s*([0-3R9])\s+', body)
            if action_inline and not body.startswith(action_inline.group(0) + '*'):
                actions = action_inline.group(1)
                body = body[action_inline.end():].strip()

        # --- Traits (entre parenthèses en début de description) ---
        traits = []
        traits_match = re.match(r'^\s*\(([^)]+)\)[\.:]?\s*', body)
        if traits_match:
            traits = [t.strip() for t in traits_match.group(1).split(',') if t.strip()]
            body = body[traits_match.end():].strip()

        # --- Conditions ---
        conditions = None
        cond_match = re.search(r'\*\*Conditions?\.\*\*\s*(.*?)(?=\s*[;\.]\s*\*\*|$)', body, re.DOTALL | re.IGNORECASE)
        if cond_match:
            conditions = clean_text(cond_match.group(1))

        # --- Déclencheur ---
        trigger = None
        trigger_match = re.search(
            r'(?:\*\*Déclencheur\.?\*\*|Déclencheur\.)\s*(.*?)(?=\s*(?:\*\*Effet|Effet\.)|$)',
            body, re.DOTALL | re.IGNORECASE
        )
        if trigger_match:
            trigger = clean_text(trigger_match.group(1))

        # --- Effet ---
        effect = None
        effect_match = re.search(
            r'(?:\*\*Effet\.?\*\*|Effet\.)\s*(.*)',
            body, re.DOTALL | re.IGNORECASE
        )
        if effect_match:
            effect = clean_text(effect_match.group(1))

        # --- Description (texte avant déclencheur/effet) ---
        description = None
        if trigger_match or effect_match or cond_match:
            first_split = min(
                m2.start() for m2 in [trigger_match, effect_match, cond_match] if m2
            )
            desc_raw = body[:first_split].strip()
        else:
            desc_raw = body.strip()

        # Nettoie les fragments résiduels de navigation
        desc_raw = re.sub(r'\n\s+[A-Z]{1,2}\n', '\n', desc_raw)
        description = clean_text(desc_raw) if desc_raw else None

        # Ignore les entrées vides ou trop courtes (artefacts)
        if not description and not effect and not trigger:
            continue

        ability_id = generate_slug('ability', raw_name)

        abilities.append({
            'id': ability_id,
            'name': raw_name,
            'actions': actions,
            'traits': traits,
            'conditions': conditions,
            'trigger': trigger,
            'effect': effect,
            'description': description,
        })

    print(f"[PARSING] {len(abilities)} capacités extraites.")
    return abilities


# ==========================================
# GÉNÉRATION XML
# ==========================================

def generate_abilities_xml(abilities, output_path):
    """Génère le fichier abilities.xml à partir de la liste de capacités."""
    print(f"[XML] Génération de {output_path}...")

    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    root = etree.Element("abilities", nsmap={'xsi': XSI_NS})
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../schema/ability.xsd")

    for ab in abilities:
        ab_node = etree.SubElement(root, "ability", id=ab['id'])

        etree.SubElement(ab_node, "name").text = ab['name']

        if ab['actions'] is not None:
            etree.SubElement(ab_node, "actions").text = ab['actions']

        if ab['traits']:
            traits_node = etree.SubElement(ab_node, "traits")
            for t in ab['traits']:
                etree.SubElement(traits_node, "trait").text = t

        if ab['conditions']:
            etree.SubElement(ab_node, "conditions").text = ab['conditions']

        if ab['trigger']:
            etree.SubElement(ab_node, "trigger").text = ab['trigger']

        if ab['effect']:
            etree.SubElement(ab_node, "effect").text = ab['effect']

        if ab['description']:
            etree.SubElement(ab_node, "description").text = ab['description']

    # Écriture
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

    print(f"[XML] Fichier écrit : {output_path} ({len(abilities)} capacités)")


# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/ldm_full/PF2R_03_Livre_des_monstres_web_v1.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/abilities/abilities.xml"

    if not os.path.exists(input_file):
        print(f"[ERROR] Fichier introuvable : {input_file}")
        sys.exit(1)

    print(f"[MAIN] Lecture de {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    abilities = parse_abilities_md(md_content)

    if abilities:
        generate_abilities_xml(abilities, output_file)

        # Validation XSD
        xsd_file = "schema/ability.xsd"
        if os.path.exists(xsd_file):
            sys.path.insert(0, os.path.dirname(__file__))
            from xml_validator import validate_xml
            validate_xml(output_file, xsd_file)
    else:
        print("[MAIN] Aucune capacité extraite.")
