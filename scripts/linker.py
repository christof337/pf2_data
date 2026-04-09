"""
scripts/linker.py

Post-processing : parcourt les XMLs monstres et sorts, et ajoute des attributs
ref= sur les éléments dont le contenu correspond à une entité connue :

  <trait>   → ref="trait-{slug}"   (depuis data/traits/traits.xml)
  <spell>   → ref="spell-{slug}"   (depuis data/spells/all_spells.xml)
  <spellRef>→ ref="spell-{slug}"   (idem, avec skip des auto-références)
  <special> → ref="ability-{slug}" (depuis data/abilities/abilities.xml)

Les éléments sans correspondance sont laissés sans ref et listés dans le rapport.

Usage:
  uv run scripts/linker.py               # traitement complet
  uv run scripts/linker.py --dry-run     # rapport sans écriture
"""

import os
import sys
from collections import defaultdict
from lxml import etree

sys.path.insert(0, os.path.dirname(__file__))
from slug_generator import generate_slug

TRAITS_XML    = "./data/traits/traits.xml"
ABILITIES_XML = "./data/abilities/abilities.xml"
MONSTERS_DIR  = "./data/monsters"
SPELLS_XML    = "./data/spells/all_spells.xml"

RARITY_REFS = {"trait-commune", "trait-peu-courante", "trait-peu-courant", "trait-rare", "trait-unique"}


# ==========================================
# INDEX LOADERS
# ==========================================

def load_xml_index(path, element_tag, prefix):
    """
    Construit un index { generate_slug(prefix, name) → id } depuis un fichier XML.

    path        : chemin vers le fichier XML
    element_tag : tag des éléments enfants directs (ex: "trait", "spell", "ability")
    prefix      : préfixe de slug (ex: "trait", "spell", "ability")
    """
    tree = etree.parse(path)
    index = {}
    for elem in tree.getroot().findall(element_tag):
        name = elem.findtext("name", "").strip()
        elem_id = elem.get("id")
        if name and elem_id:
            index[generate_slug(prefix, name)] = elem_id
    return index


# ==========================================
# LINKING
# ==========================================

def link_file(xml_path, trait_index, spell_index, ability_index, dry_run=False):
    """
    Ajoute ref= sur les éléments reconnus dans un fichier XML.
    Retourne (stats_dict, unresolved_dict).
    """
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(xml_path, parser)
    root = tree.getroot()

    stats = {"trait": 0, "spell": 0, "spellRef": 0, "special": 0}
    unresolved = {"trait": set(), "spell": set(), "spellRef": set(), "special": set()}
    changed = False

    # — Traits —
    for elem in root.iter("trait"):
        ref = elem.get("ref")
        if ref:
            # Trait déjà lié : s'assurer que le type rareté est posé si manquant
            if ref in RARITY_REFS and not elem.get("type"):
                elem.set("type", "rarity")
                changed = True
            continue
        text = (elem.text or "").strip()
        if not text:
            continue
        slug = generate_slug("trait", text)
        if slug in trait_index:
            elem.set("ref", trait_index[slug])
            if trait_index[slug] in RARITY_REFS:
                elem.set("type", "rarity")
            stats["trait"] += 1
            changed = True
        else:
            unresolved["trait"].add(text)

    # — Sorts (<spell> dans les spellLists des monstres) —
    for elem in root.iter("spell"):
        if elem.get("ref"):
            continue
        text = (elem.text or "").strip()
        if not text:
            continue
        slug = generate_slug("spell", text)
        if slug in spell_index:
            elem.set("ref", spell_index[slug])
            stats["spell"] += 1
            changed = True
        else:
            unresolved["spell"].add(text)

    # — SpellRef (<spellRef> dans les descriptions de sorts, avec skip auto-référence) —
    for elem in root.iter("spellRef"):
        if elem.get("ref"):
            continue
        text = (elem.text or "").strip()
        if not text:
            continue
        slug = generate_slug("spell", text)
        if slug not in spell_index:
            unresolved["spellRef"].add(text)
            continue
        # Skip auto-référence : si le spellRef est dans un sort qui a le même id
        parent_spell = next(elem.iterancestors("spell"), None)
        if parent_spell is not None and parent_spell.get("id") == spell_index[slug]:
            continue
        elem.set("ref", spell_index[slug])
        stats["spellRef"] += 1
        changed = True

    # — Capacités (<special> dont le <name> matche une ability connue) —
    for elem in root.iter("special"):
        if elem.get("ref"):
            continue
        name_elem = elem.find("name")
        if name_elem is None:
            continue
        text = (name_elem.text or "").strip()
        if not text:
            continue
        slug = generate_slug("ability", text)
        if slug in ability_index:
            elem.set("ref", ability_index[slug])
            stats["special"] += 1
            changed = True
        else:
            unresolved["special"].add(text)

    if not dry_run and changed:
        tree.write(xml_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

    return stats, unresolved


# ==========================================
# MAIN
# ==========================================

def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("[LINKER] Mode dry-run — aucune écriture sur le disque.")

    print(f"[LINKER] Chargement des index...")
    trait_index   = load_xml_index(TRAITS_XML,    "trait",   "trait")
    spell_index   = load_xml_index(SPELLS_XML,    "spell",   "spell")
    ability_index = load_xml_index(ABILITIES_XML, "ability", "ability")
    print(f"[LINKER]   {len(trait_index)} traits | {len(spell_index)} sorts | {len(ability_index)} capacités\n")

    totals = defaultdict(int)
    all_unresolved = {k: defaultdict(int) for k in ("trait", "spell", "spellRef", "special")}

    # — Monstres —
    xml_files = sorted(
        os.path.join(MONSTERS_DIR, f)
        for f in os.listdir(MONSTERS_DIR)
        if f.endswith(".xml")
    )
    for path in xml_files:
        stats, unres = link_file(path, trait_index, spell_index, ability_index, dry_run)
        for k, v in stats.items():
            totals[f"monster_{k}"] += v
        for k, s in unres.items():
            for t in s:
                all_unresolved[k][t] += 1

    print(f"[LINKER] ✓ Monstres ({len(xml_files)} fichiers) :")
    print(f"           traits={totals['monster_trait']}  sorts={totals['monster_spell']}  capacités={totals['monster_special']}")

    # — Sorts —
    if os.path.exists(SPELLS_XML):
        stats, unres = link_file(SPELLS_XML, trait_index, spell_index, ability_index, dry_run)
        for k, s in unres.items():
            for t in s:
                all_unresolved[k][t] += 1
        print(f"[LINKER] ✓ Sorts :")
        print(f"           traits={stats['trait']}  spellRefs={stats['spellRef']}")
        for k, v in stats.items():
            totals[f"spell_{k}"] += v

    grand_total = sum(totals.values())
    print(f"\n[LINKER] Total toutes entités : {grand_total} liens ajoutés.")

    # — Rapport non-résolus —
    labels = {"trait": "Traits", "spell": "Sorts (<spell>)", "spellRef": "Sorts (<spellRef>)", "special": "Capacités (<special>)"}
    for key, label in labels.items():
        d = all_unresolved[key]
        if d:
            print(f"\n[LINKER] {label} non résolus :")
            for name, count in sorted(d.items(), key=lambda x: -x[1])[:20]:
                print(f"  {count:4d}x  {name}")
            if len(d) > 20:
                print(f"  ... ({len(d) - 20} autres)")


if __name__ == "__main__":
    main()
