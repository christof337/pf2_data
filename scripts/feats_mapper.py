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

ANCESTRY_TRAITS = {
    "ELFE", "GNOME", "GOBELIN", "HALFELIN", "HUMAIN", "LÉCHI", "NAIN", "ORC",
    "CHANGELIN", "NÉPHILIM",
    "AIUVARIN", "DROMAAR",
}

MULTI_WORD_TRAITS = []  # à compléter si besoin

# ==========================================
# PRÉ-NETTOYAGE DU PDF
# ==========================================

def clean_pdf_artifacts(content):
    """Purge les filigranes, numéros de page et sommaires avant traitement."""
    content = strip_metadata(content)
    # 1. Gestion des retours à la ligne litéraux
    content = content.replace('\\n', '\n')

    # 2. Purge des numéros de page
    content = re.sub(r'\[\[PAGE \d+\]\]', '', content)

    # 3. Running heads — **NOM NOM** seul sur une ligne (nom répété deux fois = filigrane PDF)
    content = re.sub(r'(?m)^\s*\*\*([A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ\s]+?) \1\*\*\s*$', '', content)

    # 4. Suppression des légendes d'illustration + crédit artiste
    content = re.sub(
        r'(?m)^[ \t]{3,}[A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ][a-zà-ÿ][^\n]{0,45}\n[ \t]*[^\n]*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\n]*$\n?',
        '', content
    )
    content = re.sub(r'(?m)^.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}.*$\n?', '', content)

    return content

# ==========================================
# UTILITAIRES
# ==========================================

def clean_text(text):
    """Nettoie le texte PDF : retire les coupures de mots (tiret + espace) et normalise les espaces."""
    if not text: return ""
    text = re.sub(r'[\u002D\u2011]\n?\s+', '', text)  # tiret normal et tiret insécable (U+2011)
    text = re.sub(r'\*+', '', text)  # strip marqueurs markdown gras/italique résiduels
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

# ==========================================
# DÉTECTION DE CATÉGORIE
# ==========================================

def get_category(traits):
    """Retourne 'ancestry' si un trait d'ascendance est détecté, None sinon."""
    for t in traits:
        if t in ANCESTRY_TRAITS:
            return "ancestry"
    return None

# ==========================================
# PARSING DE DON
# ==========================================

def parse_feat_block(raw):
    """
    Parse un bloc de don et retourne un dictionnaire.
    Le bloc commence par ** et contient "DON N".

    Extrait :
    - NOM : avant "DON" dans le bloc gras
    - NIVEAU : le chiffre après "DON"
    - TRAITS : les mots en majuscules après "DON"
    - autres champs : selon les patterns classiques
    """
    if not raw or "DON" not in raw:
        return None

    # 1. Valider qu'on a "DON N"
    don_match = re.search(r'DON\s+(\d+)', raw)
    if not don_match:
        return None

    try:
        level = int(don_match.group(1))
    except (ValueError, TypeError):
        return None

    # 2. Extraire le nom : le texte AVANT "DON" dans le bloc gras
    # Le bloc gras commence par ** et le texte jusqu'à "DON" est le nom
    # Trouver le ** d'ouverture
    bold_open = raw.find('**')
    if bold_open == -1:
        return None

    # Tout ce qui est entre ** et "DON" (on va chercher avant le premier DON)
    don_pos = don_match.start()
    text_until_don = raw[bold_open:don_pos]

    # Supprimer les ** du début
    text_until_don = text_until_don[2:].strip()

    # Supprimer les ** de fermeture s'il y en a
    text_until_don = re.sub(r'\*\*.*$', '', text_until_don, flags=re.DOTALL).strip()

    # Nettoyer : supprimer les numéros de page (44 44, etc.)
    name_raw = re.sub(r'^\d+\s+\d+\s+', '', text_until_don).strip()
    name_raw = re.sub(r'NIVEAU\s+\d+\s+', '', name_raw).strip()

    # Filtrer les mauvais noms
    if not name_raw or len(name_raw) < 2 or re.match(r'^\d', name_raw):
        return None

    name = clean_text(name_raw)

    # 3. Actions (optionnel) : chiffre avant DON
    actions = None
    actions_match = re.search(r'([0-3]|9)\s+DON', raw)
    if actions_match:
        actions = actions_match.group(1)

    # 4. Traits : après "DON N", les mots en majuscules
    traits = []
    text_after_don = raw[don_pos:don_pos + 300]

    # Chercher une ligne avec traits (majuscules, pas "NIVEAU")
    traits_match = re.search(
        r'(?:DON\s+\d+.*?)(?:^|\s)([A-ZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ\s\-]+?)(?:\n|\*\*|$)',
        text_after_don,
        re.MULTILINE | re.DOTALL
    )
    if traits_match:
        candidate = traits_match.group(1).strip()
        # Filtrer les faux traits
        if candidate and not re.match(r'^(NIVEAU|Fréquence|Prérequis)', candidate):
            # Ne garder que les vraiment majuscules
            words = candidate.split()
            for w in words[:10]:  # Limiter à 10 mots de traits
                if w and w[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸ' and not w[-1] in '.,':
                    cand_traits = parse_traits(w)
                    traits.extend(cand_traits)

    traits = list(dict.fromkeys(traits))

    # 5. Catégorie
    category = get_category(traits)

    # 6. Champs optionnels
    prerequisites_match = re.search(r'\*\*Prérequis\*\*\s*(.+?)(?=\n\*\*|\Z)', raw, re.DOTALL)
    prerequisites = clean_value(prerequisites_match.group(1)) if prerequisites_match else None

    frequency_match = re.search(r'\*\*Fréquence\*\*\s*(.+?)(?=\n\*\*|\Z)', raw, re.DOTALL)
    frequency = clean_value(frequency_match.group(1)) if frequency_match else None

    trigger_match = re.search(r'\*\*Déclencheur\*\*\s*(.+?)(?=\n\*\*|\Z)', raw, re.DOTALL)
    trigger = clean_value(trigger_match.group(1)) if trigger_match else None

    requirement_match = re.search(r'\*\*Conditions?\*\*\s*(.+?)(?=\n\*\*|\Z)', raw, re.DOTALL)
    requirement = clean_value(requirement_match.group(1)) if requirement_match else None

    description = None
    special_match = re.search(r'\*\*Spécial\*\*\s*(.+?)(?=\n\*\*|$)', raw, re.DOTALL)
    special = clean_value(special_match.group(1)) if special_match else None

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

    results = []

    # Pattern : capture le bloc d'un don
    # Format approximatif : **[texte]** ... DON [chiffre] ... [TRAITS/autres]
    # Chercher des matchs qui contiennent "DON N"

    # Trouver tous les "DON N"
    don_pattern = r'DON\s+(\d+)'
    don_matches = list(re.finditer(don_pattern, content))

    if not don_matches:
        return results

    # Pour chaque occurrence de "DON N", on va extraire un bloc
    for i, don_match in enumerate(don_matches):
        don_pos = don_match.start()
        don_level = don_match.group(1)

        # Chercher le **NOM** qui précède ce "DON N"
        # Remonter jusqu'à max 500 chars avant pour trouver le **
        search_start = max(0, don_pos - 500)
        text_before = content[search_start:don_pos]

        # Trouver la DERNIÈRE occurrence de "**" avant DON
        # (qui ouvre un bloc gras contenant le nom du don)
        last_bold_idx = text_before.rfind('**')
        if last_bold_idx == -1:
            continue

        # Position absolue du "**" d'ouverture
        bold_open_abs = search_start + last_bold_idx

        # Chercher le "**" de fermeture (après l'ouverture)
        # ou chercher un pattern robuste : le prochain "**" qui apparaît après
        bold_close_search = content.find('**', bold_open_abs + 2)
        if bold_close_search == -1:
            # Pas de fermeture, le don est malformé
            continue

        # Extraire le texte entre ** **
        name_raw = content[bold_open_abs + 2:bold_close_search]

        # LE BLOC : depuis l'ouverture ** jusqu'au début du prochain don
        if i + 1 < len(don_matches):
            block_end = don_matches[i + 1].start()
        else:
            block_end = len(content)

        block_text = content[bold_open_abs:block_end]

        # Parser ce bloc
        parsed = parse_feat_block(block_text)
        if parsed:
            results.append(parsed)
        else:
            # Debug : si le parsing échoue, c'est que parse_feat_block n'a pas pu extraire le nom
            pass

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
        # Déduplication si collision
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
                etree.SubElement(traits_el, "trait").text = t
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
