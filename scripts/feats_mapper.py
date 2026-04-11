import re
import os
import sys
from lxml import etree

from xml_validator import validate_xml
from slug_generator import generate_slug
from utils import strip_metadata

# ==========================================
# CONFIGURATION & CONSTANTES
# ==========================================

UPPER = r'A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ'

_ANCESTRY_CORE = {
    "ELFE", "GNOME", "GOBELIN", "HALFELIN", "HUMAIN", "LÉCHI", "NAIN", "ORC",
}
_VERSATILE_HERITAGE = {"CHANGELIN", "NÉPHILIM"}
_MIXED_HERITAGE = {"AIUVARIN", "DROMAAR"}

ANCESTRY_TRAITS = _ANCESTRY_CORE | _VERSATILE_HERITAGE | _MIXED_HERITAGE

MULTI_WORD_TRAITS = []  # à compléter si besoin

# ==========================================
# PRÉ-NETTOYAGE DU PDF
# ==========================================

def clean_pdf_artifacts(content):
    """Purge les filigranes, numéros de page et sommaires avant traitement."""
    content = strip_metadata(content)
    content = content.replace('\\n', '\n')

    # Callout box _** (intro de chapitre, italic+bold non fermé)
    content = re.sub(r'\n\s*_\*\*[^\n]+(?:\n(?!\s*\[\[)[^\n]*)*', '', content)

    # Purge des marqueurs de page, flux principal, en-têtes récurrents
    content = re.sub(r'\[\[PAGE \d+\]\]', '', content)
    content = re.sub(r'(?m)^\s*# FLUX PRINCIPAL \(STATS\/BASE\)\s*$(?:\n\s*Livre des Joueurs)?\n*\*{0,2}\s*\d{1,3}\s?\d{0,3}\*{0,2}', '', content)
    content = re.sub(r'(?m)^\s*Dons\s*$', '', content, flags=re.IGNORECASE)

    # Légendes d'illustration + crédit artiste
    content = re.sub(
        r'(?m)^[ \t]{3,}[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][a-zà-ÿ][^\n]{0,45}\n[ \t]*[^\n]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\n]*$\n?',
        '', content
    )
    content = re.sub(r'(?m)^.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}.*$\n?', '', content)

    # Running heads : **MOT MOT** seul sur une ligne (nom répété deux fois = filigrane)
    content = re.sub(r'(?m)^\s*\*\*([A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ\s]+?) \1\*\*\s*$', '', content)

    # Suppression intelligente des sommaires (barres latérales de navigation)
    lines = content.split('\n')
    cleaned_lines = []
    streak = []
    empty_count = 0

    for line in lines:
        stripped = line.strip()

        if len(stripped) == 0:
            empty_count += 1
            streak.append(line)
            if empty_count >= 2:
                if len([l for l in streak if l.strip()]) >= 5:
                    pass  # jeter le sommaire
                else:
                    cleaned_lines.extend(streak)
                streak = []
        else:
            empty_count = 0
            is_short = len(stripped) < 30
            is_title = re.search(r'\b(?:DON|SORT|TOUR DE MAGIE)\s+\d+', stripped)
            ends_with_dot = stripped.endswith('.')

            if is_short and not is_title and not ends_with_dot:
                streak.append(line)
            else:
                if len([l for l in streak if l.strip()]) >= 5:
                    pass  # c'était un sommaire, on l'ignore
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
    """Nettoie le texte PDF : retire les coupures de mots et normalise les espaces."""
    if not text:
        return ""
    text = re.sub(r'[\u002D\u2011]\n?\s+', '', text)  # tirets coupure de mot
    text = re.sub(r'\*+', '', text)                    # marqueurs markdown résiduels
    return re.sub(r'\s+', ' ', text).strip()

def clean_desc(text):
    """Nettoie une description : corrige les coupures de mots, préserve le gras."""
    if not text:
        return ""
    text = re.sub(r'[\u002D\u2011]\n?\s+', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def clean_value(val):
    if not val:
        return None
    v = re.sub(r'^[:\-\s\.]+', '', clean_text(val)).strip()
    return v or None

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
# DÉTECTION DE CATÉGORIE
# ==========================================

def get_ancestry_trait_type(trait):
    """Retourne le type d'ascendance d'un trait, ou None si ce n'est pas un trait d'ascendance."""
    if trait in _ANCESTRY_CORE:
        return "ancestry"
    if trait in _VERSATILE_HERITAGE:
        return "versatile-heritage"
    if trait in _MIXED_HERITAGE:
        return "mixed-heritage"
    return None

def get_category(traits):
    """Retourne 'ancestry' si un trait d'ascendance est détecté, None sinon."""
    for t in traits:
        if t in ANCESTRY_TRAITS:
            return "ancestry"
    return None

# ==========================================
# NORMALISATION DU HEADER
# ==========================================

def _normalize_split_header(text):
    """
    Normalise le format splitté par l'extraction PDF :
    **NOM **\n    [action]\n      **       DON N\n TRAITS**
    →
    **NOM [action] DON N\n TRAITS**
    """
    return re.sub(
        r'\*\*([^*\n]+?)\s*\*\*\s*\n\s*([0-9])\s*\n\s*\*\*(\s*DON\s+\d+[^*]*)\*\*',
        r'**\1 \2 \3**',
        text,
        flags=re.DOTALL
    )

# ==========================================
# PARSING D'UN BLOC DE DON
# ==========================================

def parse_feat_block(raw):
    """
    Parse un bloc de don.

    Structure attendue (après nettoyage) :
      **NOM [action] DON N
       TRAIT1 TRAIT2
       [Prérequis. ]**[valeur_prérequis]
      Description du don.
      **Fréquence** valeur
      **Spécial** texte

    Retourne None si le bloc ne contient pas "DON N".
    """
    if not raw or 'DON' not in raw:
        return None

    # Normaliser le format splitté avant tout
    raw = _normalize_split_header(raw)

    # 1. Valider "DON N" et extraire le niveau
    don_match = re.search(r'\bDON\s+(\d+)\b', raw)
    if not don_match:
        return None
    try:
        level = int(don_match.group(1))
    except (ValueError, TypeError):
        return None

    # 2. Trouver le bloc header **...** contenant "DON N"
    #    On cherche le ** qui précède DON N puis le ** qui le ferme
    don_pos = don_match.start()

    # Chercher le ** d'ouverture : le dernier avant DON N
    text_before_don = raw[:don_pos]
    last_bold_open = text_before_don.rfind('**')
    if last_bold_open == -1:
        return None

    # Chercher la fermeture ** après le niveau
    bold_close = raw.find('**', don_pos)
    if bold_close == -1:
        # Pas de fermeture → prendre tout jusqu'à la fin de la première ligne longue
        header_content = raw[last_bold_open + 2:]
        body = ''
    else:
        header_content = raw[last_bold_open + 2:bold_close]
        body = raw[bold_close + 2:]

    # 3. Extraire le nom depuis le header
    # Tout ce qui précède "DON" dans le header content
    header_before_don = header_content[:header_content.find('DON')]

    # Supprimer les artefacts : numéros de page (44 44), NIVEAU N, chiffre d'action en fin
    name_raw = re.sub(r'^\d+\s+\d+\s+', '', header_before_don.strip())
    name_raw = re.sub(r'^NIVEAU\s+\d+\s+', '', name_raw)
    name_raw = re.sub(r'\s+[0-9]\s*$', '', name_raw)  # chiffre d'action après normalisation
    name_raw = name_raw.strip()

    if not name_raw or len(name_raw) < 2 or re.match(r'^\d', name_raw):
        return None

    name = clean_text(name_raw)

    # 4. Actions : chiffre 0–3 ou 9 immédiatement avant DON
    actions = None
    actions_match = re.search(r'([0-9])\s+DON', header_content)
    if actions_match:
        actions = actions_match.group(1)

    # 5. Traits : tout ce qui suit "DON N" dans le header, jusqu'à un champ nommé ou la fin
    #    Format : après "DON N\n TRAIT1 TRAIT2\n [Prérequis.]"
    header_after_don = re.sub(r'^.*?\bDON\s+\d+\s*', '', header_content, flags=re.DOTALL)

    # Les traits sont la première ligne du reste (avant un éventuel "Prérequis")
    traits_raw = re.split(r'\n\s*(?:Prérequis|Fréquence|Déclencheur|Conditions?)', header_after_don, maxsplit=1)[0]
    traits = parse_traits(traits_raw.strip())

    # 6. Catégorie
    category = get_category(traits)

    # 7. Prérequis : peut être dans le header ("Prérequis." avant **) ou dans le body
    #    Dans le header : header_after_don contient "Prérequis. " + le reste qui est dans body
    prerequisites = None

    # Cas header : "Prérequis." dans le header_content → la valeur est au début de body
    prereq_in_header = re.search(r'(?:Prérequis|Prérequis\.)\s*$', header_content, re.IGNORECASE)
    if prereq_in_header:
        # La valeur est sur la première ligne du body (toujours une ligne courte)
        prereq_val_match = re.match(r'\s*([^\n]+)', body)
        if prereq_val_match:
            prerequisites = clean_value(prereq_val_match.group(1))
            # Avancer le body après cette première ligne
            body = body[prereq_val_match.end():]
    else:
        # Cas body : **Prérequis** ou **Prérequis.**
        prereq_body = re.search(r'\*\*Prérequis\.?\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
        if prereq_body:
            prerequisites = clean_value(prereq_body.group(1))

    # 8. Autres champs dans le body
    frequency_match = re.search(r'\*\*Fréquence\.?\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
    frequency = clean_value(frequency_match.group(1)) if frequency_match else None

    trigger_match = re.search(r'\*\*Déclencheur\.?\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
    trigger = clean_value(trigger_match.group(1)) if trigger_match else None

    requirement_match = re.search(r'\*\*Conditions?\.?\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
    requirement = clean_value(requirement_match.group(1)) if requirement_match else None

    special_match = re.search(r'\*\*Spécial\.?\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
    special = clean_value(special_match.group(1)) if special_match else None

    # 9. Description : ce qui reste dans le body après avoir retiré les champs nommés
    #    et la valeur de prérequis déjà consommée
    desc_body = body

    # Supprimer la valeur de prérequis si elle était en début de body (déjà consommée)
    if prereq_in_header and prerequisites:
        pass  # body a déjà été avancé

    # Supprimer tous les champs nommés du body pour isoler la description
    desc_clean = re.sub(
        r'\*\*(?:Prérequis|Fréquence|Déclencheur|Conditions?|Spécial)\.?\*\*\s*.+?(?=\n\s*\*\*|\Z)',
        '', desc_body, flags=re.DOTALL
    )
    description = clean_desc(desc_clean) or None

    return {
        'name': name,
        'level': level,
        'actions': actions,
        'traits': traits,
        'category': category,
        'prerequisites': prerequisites,
        'frequency': frequency,
        'trigger': trigger,
        'requirement': requirement,
        'description': description,
        'special': special,
    }

# ==========================================
# PARSING GLOBAL
# ==========================================

def parse_feats_md(content):
    """Parse le contenu MD et retourne une liste de dictionnaires de dons."""
    content = clean_pdf_artifacts(content)

    # Normaliser les headers splittés AVANT la découpe en blocs, sinon
    # le split_pat ne peut pas les détecter (le chiffre d'action est hors du **)
    content = _normalize_split_header(content)

    # Découpe : chaque don commence par **[MAJUSCULE(S)]... DON N
    # Après normalisation, le chiffre d'action est inclus dans le **...**
    split_pat = re.compile(
        rf'(?=\s*\*\*[{UPPER}][^*\n]{{2,}}(?:\s+[0-9]\s+|\s+)DON\s+\d)',
        re.MULTILINE
    )
    blocks = split_pat.split(content)

    results = []
    for block in blocks:
        block = block.strip()
        if not block or 'DON' not in block:
            continue
        parsed = parse_feat_block(block)
        if parsed:
            results.append(parsed)
    return results

# ==========================================
# GÉNÉRATION XML
# ==========================================

def generate_feats_xml(feats_data, output_path):
    """Génère le fichier XML des dons à partir des données parsées."""
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    root = etree.Element("feats", nsmap={'xsi': XSI})
    root.set(f'{{{XSI}}}noNamespaceSchemaLocation', '../../schema/feat.xsd')

    seen_ids = set()
    for f in feats_data:
        feat_id = generate_slug("feat", f['name'])
        if feat_id in seen_ids:
            feat_id += "-2"
        seen_ids.add(feat_id)

        feat_el = etree.SubElement(root, "feat", id=feat_id, type="don")
        if f.get('category'):
            feat_el.set('category', f['category'])

        etree.SubElement(feat_el, "name").text = f['name']
        if f.get('level') is not None:
            etree.SubElement(feat_el, "level").text = str(f['level'])
        if f.get('actions') is not None:
            etree.SubElement(feat_el, "actions").text = f['actions']
        if f.get('traits'):
            traits_el = etree.SubElement(feat_el, "traits")
            for t in f['traits']:
                trait_type = get_ancestry_trait_type(t)
                attrs = {"type": trait_type} if trait_type else {}
                etree.SubElement(traits_el, "trait", **attrs).text = t
        if f.get('prerequisites'):
            etree.SubElement(feat_el, "prerequisites").text = f['prerequisites']
        if f.get('frequency'):
            etree.SubElement(feat_el, "frequency").text = f['frequency']
        if f.get('trigger'):
            etree.SubElement(feat_el, "trigger").text = f['trigger']
        if f.get('requirement'):
            etree.SubElement(feat_el, "requirement").text = f['requirement']
        if f.get('description'):
            etree.SubElement(feat_el, "description").text = f['description']
        if f.get('special'):
            etree.SubElement(feat_el, "special").text = f['special']

    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/dons/test_dons.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./output/dons/dons_ldj.xml"
    content = open(input_file, encoding='utf-8').read()
    data = parse_feats_md(content)
    generate_feats_xml(data, output_file)
    validate_xml(output_file, "./schema/feat.xsd")
