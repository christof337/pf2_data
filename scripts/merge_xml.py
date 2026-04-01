"""
merge_xml.py — Fusion de fichiers XML par attribut id.

Usage:
    uv run scripts/merge_xml.py <base.xml> <patch.xml> [patch2.xml ...] <output.xml>

- Merge les éléments enfants directs par attribut `id`.
- En cas de doublon :
    * Si la base a une <description> vide et le patch une non-vide → on enrichit la base.
    * Si les deux ont une <description> non-vide différente → on garde la base et on log le conflit.
    * Sinon → on ignore le patch (base gagne).
- Les nouveaux éléments du/des patch(s) sont ajoutés à la fin.
"""

import sys
import os
from lxml import etree


def _get_desc(elem):
    """Retourne le texte de <description>, ou '' si absent/vide."""
    return (elem.findtext("description") or "").strip()


def merge_xml_files(base_path, patch_paths, output_path):
    parser = etree.XMLParser(remove_blank_text=True)

    base_tree = etree.parse(base_path, parser)
    base_root = base_tree.getroot()

    # Index id → element pour les lookups rapides
    base_index = {
        elem.get("id"): elem
        for elem in base_root
        if elem.get("id")
    }

    for patch_path in patch_paths:
        patch_tree = etree.parse(patch_path, parser)
        patch_root = patch_tree.getroot()

        added = enriched = skipped = conflicts = 0

        for elem in patch_root:
            elem_id = elem.get("id")
            if not elem_id or elem_id not in base_index:
                base_root.append(elem)
                if elem_id:
                    base_index[elem_id] = elem
                added += 1
                continue

            # Doublon — arbitrage par description
            base_elem = base_index[elem_id]
            base_desc = _get_desc(base_elem)
            patch_desc = _get_desc(elem)

            if not base_desc and patch_desc:
                # Enrichissement : on injecte la description du patch dans la base
                base_desc_el = base_elem.find("description")
                patch_desc_el = elem.find("description")
                if base_desc_el is not None and patch_desc_el is not None:
                    base_desc_el.text = patch_desc_el.text
                enriched += 1
            elif base_desc and patch_desc and base_desc != patch_desc:
                print(f"[MERGE] ⚠ conflit '{elem_id}' : descriptions différentes, on garde la base.")
                conflicts += 1
            else:
                skipped += 1

        parts = [f"+{added} nouveaux"]
        if enriched:  parts.append(f"+{enriched} enrichis")
        if conflicts: parts.append(f"{conflicts} conflits (base gardée)")
        if skipped:   parts.append(f"{skipped} doublons ignorés")
        print(f"[MERGE] {patch_path} → {', '.join(parts)}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    base_tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"[MERGE] ✓ Résultat écrit dans {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: merge_xml.py <base.xml> <patch.xml> [patch2.xml ...] <output.xml>")
        sys.exit(1)

    *inputs, output = sys.argv[1:]
    base = inputs[0]
    patches = inputs[1:]

    merge_xml_files(base, patches, output)
