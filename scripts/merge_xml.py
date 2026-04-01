"""
merge_xml.py — Fusion de fichiers XML par attribut id.

Usage:
    uv run scripts/merge_xml.py <base.xml> <patch.xml> [patch2.xml ...] <output.xml>

- Merge les éléments enfants directs par attribut `id`.
- Priorité au premier fichier (base) en cas de doublon : les éléments existants
  (avec leurs ref= déjà posés par le linker) ne sont jamais écrasés.
- Les nouveaux éléments du/des patch(s) sont ajoutés à la fin.
"""

import sys
import os
from lxml import etree


def merge_xml_files(base_path, patch_paths, output_path):
    parser = etree.XMLParser(remove_blank_text=True)

    base_tree = etree.parse(base_path, parser)
    base_root = base_tree.getroot()

    # Construire l'index des ids existants
    existing_ids = {
        elem.get("id")
        for elem in base_root
        if elem.get("id")
    }

    added = 0
    skipped = 0

    for patch_path in patch_paths:
        patch_tree = etree.parse(patch_path, parser)
        patch_root = patch_tree.getroot()

        for elem in patch_root:
            elem_id = elem.get("id")
            if elem_id and elem_id in existing_ids:
                skipped += 1
            else:
                base_root.append(elem)
                if elem_id:
                    existing_ids.add(elem_id)
                added += 1

        print(f"[MERGE] {patch_path} → +{added} nouveaux, {skipped} doublons ignorés")
        added = 0
        skipped = 0

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
