"""
utils.py — Utilitaires partagés entre les mappers PF2e.

Fonctions communes à monster_mapper et trait_mapper.
Les versions spécialisées de clean_text (spells_mapper, ability_mapper)
restent locales car elles ont un comportement différent :
  - spells_mapper : retire les coupures de mots PDF (tiret + espace)
  - ability_mapper : préserve les sauts de ligne, supprime les caractères °/\ufffd
"""

import re


def clean_text(text):
    """Normalise les espaces et sauts de ligne : collapse tout whitespace en un espace."""
    return re.sub(r'\s+', ' ', text).strip()
