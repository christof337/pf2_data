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
    # FLUX PRINCIPAL : on supprime le bloc jusqu'aux lignes vides incluses,
    # MAIS on conserve **NN NN** (numéro de page suivante) pour que Rule 3
    # du parser puisse tronquer la description au bon endroit.
    content = re.sub(r'(?m)^\s*# FLUX PRINCIPAL \(STATS\/BASE\)\s*$(?:\n\s*Livre des Joueurs)?\n*', '', content)
    # Purge des numéros de page en gras **NN NN (ouverture de span bold sans fermeture sur la ligne)
    content = re.sub(r'\*\*\d+\s+\d+\s*\n', '', content)
    # Purge des en-têtes de chapitre récurrents (running heads après page break)
    content = re.sub(r'(?m)^\s*Ascendances\s*&\s*Historiques\s*$', '', content)
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
    """Détermine la catégorie d'un don selon ses traits."""
    for t in traits:
        if t in ANCESTRY_TRAITS:
            return "ancestry"
    if "GÉNÉRAL" in traits and "COMPÉTENCE" in traits:
        return "skill"
    if "GÉNÉRAL" in traits:
        return "general"
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
# SOUS-ACTIVITÉS CONFÉRÉES
# ==========================================

# Détecte **NomAction**\n[digit]\n — ne matche PAS les headers de dons (pas de "DON N")
_GRANTED_ACTIVITY_PAT = re.compile(
    r'\*\*([^*\n]+?)\*\*\s*\n\s*([0-9])\s*\n'
)

def _extract_granted_activities(body):
    """
    Extrait les sous-activités imbriquées dans le body d'un don.
    Format reconnu :
      **NomAction**
          [0-9]
           **Conditions.** texte ; **Effet.**
      Description de l'activité.
    Retourne (liste_granted_activities, body_principal_nettoyé).
    """
    splits = list(_GRANTED_ACTIVITY_PAT.finditer(body))
    if not splits:
        return [], body

    # Le body principal s'arrête avant la première sous-activité
    main_body = body[:splits[0].start()]

    activities = []
    for i, m in enumerate(splits):
        sub_name = clean_text(m.group(1))
        sub_actions = m.group(2)

        end = splits[i + 1].start() if i + 1 < len(splits) else len(body)
        sub_content = body[m.end():end]

        # Requirement (Conditions)
        req_m = re.search(
            rf'\*\*Conditions?\.?\s*\*\*\s*(.+?)(?=\n\n|\n\s*\*\*|\n\s*[{UPPER}]|\Z)',
            sub_content, re.DOTALL
        )
        sub_req = clean_value(req_m.group(1)) if req_m else None
        # Supprimer le label "Effet." en fin de valeur (artefact PDF)
        if sub_req:
            sub_req = re.sub(r'\s*;\s*Effet\.?\s*$', '', sub_req, flags=re.IGNORECASE).strip() or None

        # Description = ce qui suit le requirement (ou tout le contenu si absent)
        desc_raw = sub_content[req_m.end():] if req_m else sub_content
        desc_raw = re.sub(
            rf'\*\*(?:Fréquence|Déclencheur|Conditions?|Spécial)\.?\s*\*\*\s*.+?(?=\n\n|\n\s*\*\*|\n\s*[{UPPER}]|\Z)',
            '', desc_raw, flags=re.DOTALL
        )
        sub_desc = clean_desc(desc_raw) or None

        activities.append({
            'name': sub_name,
            'actions': sub_actions,
            'requirement': sub_req,
            'description': sub_desc,
        })

    return activities, main_body

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

    # 7. Extraire les sous-activités conférées AVANT de parser les mécaniques du don principal
    #    (évite que **Conditions.** d'une sous-activité soit capturé comme requirement du don)
    granted_activities, body = _extract_granted_activities(body)

    # 8. Champs qui peuvent se terminer dans le header (après normalisation split)
    #    Quand _normalize_split_header capture un nom de champ à l'intérieur des **,
    #    la VALEUR de ce champ se retrouve en début de body sans marqueur **Champ**.
    #    Exemples : header se termine par "Fréquence" → body commence par "une fois toutes les 10 min"
    prerequisites = None
    frequency = None
    trigger = None
    requirement = None

    field_in_header = re.search(
        r'(Prérequis|Fréquence|Déclencheur|Conditions?)\.?\s*$',
        header_content, re.IGNORECASE
    )
    if field_in_header:
        field_name = field_in_header.group(1).lower()
        # La valeur est sur la première ligne du body (parfois deux lignes si coupure de mot)
        val_match = re.match(r'\s*([^\n]+)', body)
        if val_match:
            val_raw = val_match.group(1)
            body_rest = body[val_match.end():]
            # Continuation sur la ligne suivante si coupure de mot par tiret
            if re.search(r'[\u002D\u2011]\s*$', val_raw):
                cont = re.match(r'\n\s*([^\n]+)', body_rest)
                if cont:
                    val_raw = val_raw + '\n' + cont.group(1)
                    body_rest = body_rest[cont.end():]
            val = clean_value(val_raw)
            body = body_rest
            if 'prérequis' in field_name:
                prerequisites = val
            elif field_name == 'fréquence':
                frequency = val
            elif field_name == 'déclencheur':
                trigger = val
            elif 'condition' in field_name:
                requirement = val
    else:
        # Cas body : **Prérequis** ou **Prérequis.** ou **Prérequis. ** (espace avant fermeture)
        prereq_body = re.search(rf'\*\*Prérequis\.?\s*\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*[{UPPER}]|\Z)', body, re.DOTALL)
        if prereq_body:
            prerequisites = clean_value(prereq_body.group(1))

    # 9. Autres champs dans le body (complètent ou remplacent les valeurs ci-dessus si absentes)
    if frequency is None:
        frequency_match = re.search(rf'\*\*Fréquence\.?\s*\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*[{UPPER}]|\Z)', body, re.DOTALL)
        frequency = clean_value(frequency_match.group(1)) if frequency_match else None

    if trigger is None:
        trigger_match = re.search(rf'\*\*Déclencheur\.?\s*\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*[{UPPER}]|\Z)', body, re.DOTALL)
        trigger = clean_value(trigger_match.group(1)) if trigger_match else None

    if requirement is None:
        requirement_match = re.search(rf'\*\*Conditions?\.?\s*\*\*\s*(.+?)(?=\n\s*\*\*|\n\s*[{UPPER}]|\Z)', body, re.DOTALL)
        requirement = clean_value(requirement_match.group(1)) if requirement_match else None

    special_match = re.search(rf'\*\*Spécial\.?\s*\*\*\s*(.+?)(?=\n\s*\*\*|\Z)', body, re.DOTALL)
    special = clean_value(special_match.group(1)) if special_match else None

    # 9. Description : ce qui reste dans le body après avoir retiré les champs nommés
    #    et la valeur de prérequis déjà consommée
    desc_body = body

    # body a déjà été avancé au-delà de la valeur du champ si field_in_header était non-None

    # Supprimer tous les champs nommés du body pour isoler la description
    desc_clean = re.sub(
        rf'\*\*(?:Prérequis|Fréquence|Déclencheur|Conditions?|Spécial)\.?\s*\*\*\s*.+?(?=\n\s*\*\*|\n\s*[{UPPER}]|\Z)',
        '', desc_body, flags=re.DOTALL
    )
    # Règle 3 en premier : tronquer à **NN NN** (numéro de page = frontière de section)
    # Doit précéder Rule 1 car Rule 1 peut consumer le ** fermant de **NN NN**
    # via \*\*\s*[UPPER] si le saut de ligne suivant mène à une majuscule.
    desc_clean = re.sub(r'\*\*\d+\s+\d+\*\*.*', '', desc_clean, flags=re.DOTALL)
    # ⚠️ : règles 1 et 2 si dessous risquées, peuvent masquer des problèmes de découpage, faire perdre un spécial etc
    # Règle 1 : tronquer à **[MAJUSCULE] (début d'un autre don fusionné)
    desc_clean = re.sub(rf'\*\*\s*[{UPPER}].*', '', desc_clean, flags=re.DOTALL)
    # Règle 2 : tronquer à une ligne MAJUSCULES DON N (don non découpé fusionné)
    desc_clean = re.sub(rf'(?m)^\s*[{UPPER}]{{2,}}[{UPPER}\u2019\' ]*\s+DON\s+\d.*', '', desc_clean, flags=re.DOTALL)
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
        'granted_activities': granted_activities,
    }

# ==========================================
# PARSING GLOBAL
# ==========================================

def parse_feats_md(content, quiet=False):
    """Parse le contenu MD et retourne une liste de dictionnaires de dons."""
    content = clean_pdf_artifacts(content)

    # Supprimer les préfixes NIVEAU N qui précèdent le nom du don à l'intérieur
    # d'un header gras (**NIVEAU 5\nNOM DON N → **NOM DON N).
    # Gère aussi le cas avec numéro de page : **44 44\nNIVEAU 1\nNOM DON N → **NOM DON N
    content = re.sub(r'\*\*(?:\d+\s+\d+\s*\n\s*)?NIVEAU\s+\d+\s*\n\s*', '**', content)
    # Supprimer les lignes NIVEAU N autonomes (pas de ** avant — running heads résiduels)
    content = re.sub(r'(?m)^\s*NIVEAU\s+\d+\s*$\n?', '', content)

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

def generate_feats_xml(feats_data, output_path, quiet=False):
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

        # --- Champs hérités de activityType (ordre du schéma) ---
        etree.SubElement(feat_el, "name").text = f['name']
        if f.get('actions') is not None:
            etree.SubElement(feat_el, "actions").text = f['actions']
        if f.get('traits'):
            traits_el = etree.SubElement(feat_el, "traits")
            for t in f['traits']:
                trait_type = get_ancestry_trait_type(t)
                attrs = {"type": trait_type} if trait_type else {}
                etree.SubElement(traits_el, "trait", **attrs).text = t
        if f.get('frequency'):
            etree.SubElement(feat_el, "frequency").text = f['frequency']
        if f.get('trigger'):
            etree.SubElement(feat_el, "trigger").text = f['trigger']
        if f.get('requirement'):
            etree.SubElement(feat_el, "requirement").text = f['requirement']
        etree.SubElement(feat_el, "description").text = f.get('description') or ''
        # --- Champs de l'extension featType ---
        if f.get('level') is not None:
            etree.SubElement(feat_el, "level").text = str(f['level'])
        if f.get('prerequisites'):
            etree.SubElement(feat_el, "prerequisites").text = f['prerequisites']
        if f.get('special'):
            etree.SubElement(feat_el, "special").text = f['special']
        for ga in f.get('granted_activities') or []:
            ga_el = etree.SubElement(feat_el, "grantedActivity")
            etree.SubElement(ga_el, "name").text = ga['name']
            if ga.get('actions'):
                etree.SubElement(ga_el, "actions").text = ga['actions']
            if ga.get('requirement'):
                etree.SubElement(ga_el, "requirement").text = ga['requirement']
            etree.SubElement(ga_el, "description").text = ga.get('description') or ''

    tree = etree.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/dons/test_dons.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./output/dons/dons_ldj.xml"
    content = open(input_file, encoding='utf-8').read()
    data = parse_feats_md(content)
    generate_feats_xml(data, output_file)
    validate_xml(output_file, "./schema/feat.xsd")
