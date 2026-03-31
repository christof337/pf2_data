import os
import difflib
import tempfile
import sys

sys.path.append(os.path.relpath("scripts"))

from monster_mapper import parse_monster_md, generate_monster_xml
from spells_mapper import parse_spells_md, generate_spells_xml

def run_snapshot_test(name, md_path, expected_xml_path, parse_fn, generate_fn):
    print(f"▶ Exécution du test : {name}...")

    # 1. Lecture des fichiers
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    with open(expected_xml_path, 'r', encoding='utf-8') as f:
        expected_xml = f.read()

    # 2. Exécution du mapper dans un fichier temporaire
    data = parse_fn(md_content)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_output = os.path.join(tmpdirname, "actual_output.xml")
        generate_fn(data, temp_output)

        with open(temp_output, 'r', encoding='utf-8') as f:
            actual_xml = f.read()

    # 3. Comparaison
    if actual_xml == expected_xml:
        print(f"  ✅ SUCCÈS : Le XML généré est identique au Snapshot.\n")
        return True
    else:
        print(f"  ❌ ÉCHEC : Régression détectée !")
        print("  --- Différences (Attendu vs Actuel) ---")

        diff = difflib.unified_diff(
            expected_xml.splitlines(),
            actual_xml.splitlines(),
            fromfile='Attendu (Snapshot)',
            tofile='Actuel (Généré)',
            lineterm=''
        )
        for line in diff:
            if line.startswith('-') and not line.startswith('---'):
                print(f"\033[91m{line}\033[0m")
            elif line.startswith('+') and not line.startswith('+++'):
                print(f"\033[92m{line}\033[0m")
            else:
                print(line)
        print("\n")
        return False

if __name__ == "__main__":
    print("="*50)
    print("LANCEMENT DES TESTS DE NON-RÉGRESSION")
    print("="*50)

    tests = [
        {
            "name": "Jeune Dragon Empyréen (Monstre Standard)",
            "md": "./tests/fixtures/test_dragon.md",
            "xml": "./tests/fixtures/test_dragon_ok.xml",
            "parse": parse_monster_md,
            "generate": generate_monster_xml,
        },
        {
            "name": "Sorts (all_spells.xml complet)",
            "md": "./tests/fixtures/test_sorts.md",
            "xml": "./tests/fixtures/test_sorts_ok.xml",
            "parse": parse_spells_md,
            "generate": generate_spells_xml,
        },
    ]

    all_passed = True
    for t in tests:
        if not run_snapshot_test(t["name"], t["md"], t["xml"], t["parse"], t["generate"]):
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT AU VERT ! Tu peux continuer à coder sereinement.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ. Vérifie tes modifications (ou mets à jour tes Snapshots si le changement est voulu).")