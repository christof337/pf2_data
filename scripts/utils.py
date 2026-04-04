"""
utils.py — Utilitaires partagés entre les mappers PF2e.

Fonctions communes à monster_mapper et trait_mapper.
Les versions spécialisées de clean_text (spells_mapper, ability_mapper)
restent locales car elles ont un comportement différent :
  - spells_mapper : retire les coupures de mots PDF (tiret + espace)
  - ability_mapper : préserve les sauts de ligne, supprime les caractères °/\ufffd
"""

import re


def strip_metadata(content):
    """Supprime le bloc [[METADATA]]...[[/METADATA]] en tête des MD extraits."""
    return re.sub(r'^\[\[METADATA\]\].*?\[\[/METADATA\]\]\n?', '', content, flags=re.DOTALL)


def clean_text(text):
    """Normalise les espaces et sauts de ligne : collapse tout whitespace en un espace."""
    return re.sub(r'\s+', ' ', text).strip()


def parse_table_markers(content):
    """Extrait les blocs [[TABLE_START]]...[[TABLE_END]] du contenu MD.
    Retourne (content_sans_tables, tables) où tables est une liste de dicts
    {'header': [...], 'rows': [[...], ...]}."""
    tables = []

    def _extract_table(m):
        table = {'header': [], 'rows': []}
        for line in m.group(0).splitlines():
            if line.startswith('[[TABLE_HEADER]]'):
                table['header'] = [c.replace('\\|', '|') for c in line[len('[[TABLE_HEADER]]'):].split('|')]
            elif line.startswith('[[TABLE_ROW]]'):
                table['rows'].append([c.replace('\\|', '|') for c in line[len('[[TABLE_ROW]]'):].split('|')])
        tables.append(table)
        return ''

    content = re.sub(r'\[\[TABLE_START\]\].*?\[\[TABLE_END\]\]', _extract_table, content, flags=re.DOTALL)
    return content, tables


def split_bullet_list(text):
    """Sépare un texte contenant des bullets (•) en (intro_brut, [items_bruts]).
    Ne nettoie pas le texte — le caller applique sa propre fonction de nettoyage.
    Retourne (text, []) si aucun • n'est trouvé."""
    if '•' not in text:
        return text, []
    parts = re.split(r'\s*•\s*', text)
    intro = parts[0]
    items = [p for p in parts[1:] if p.strip()]
    return intro, items
