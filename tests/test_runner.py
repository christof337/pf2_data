import os
import difflib
import tempfile
import sys

sys.path.append(os.path.relpath("scripts"))

from monster_mapper import parse_monster_md, generate_monster_xml
from spells_mapper import parse_spells_md, generate_spells_xml


def _run_diff(expected_xml, actual_xml):
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


def run_snapshot_test(name, md_path, expected_xml_path):
    print(f"▶ Exécution du test : {name}...")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    with open(expected_xml_path, 'r', encoding='utf-8') as f:
        expected_xml = f.read()

    data = parse_monster_md(md_content)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_output = os.path.join(tmpdirname, "actual_output.xml")
        generate_monster_xml(data, temp_output)
        with open(temp_output, 'r', encoding='utf-8') as f:
            actual_xml = f.read()

    if actual_xml == expected_xml:
        print(f"  ✅ SUCCÈS : Le XML généré est identique au Snapshot.\n")
        return True
    else:
        print(f"  ❌ ÉCHEC : Régression détectée !")
        print("  --- Différences (Attendu vs Actuel) ---")
        _run_diff(expected_xml, actual_xml)
        return False


def run_snapshot_test_spells(name, md_path, expected_xml_path):
    print(f"▶ Exécution du test : {name}...")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    with open(expected_xml_path, 'r', encoding='utf-8') as f:
        expected_xml = f.read()

    spells_data = parse_spells_md(md_content)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_output = os.path.join(tmpdirname, "actual_output.xml")
        generate_spells_xml(spells_data, temp_output)
        with open(temp_output, 'r', encoding='utf-8') as f:
            actual_xml = f.read()

    if actual_xml == expected_xml:
        print(f"  ✅ SUCCÈS : Le XML généré est identique au Snapshot.\n")
        return True
    else:
        print(f"  ❌ ÉCHEC : Régression détectée !")
        print("  --- Différences (Attendu vs Actuel) ---")
        _run_diff(expected_xml, actual_xml)
        return False


if __name__ == "__main__":
    print("="*50)
    print("LANCEMENT DES TESTS DE NON-RÉGRESSION")
    print("="*50)

    monster_tests = [
        {
            "name": "Jeune Dragon Empyréen (Monstre Standard)",
            "md": "./tests/fixtures/test_dragon.md",
            "xml": "./tests/fixtures/test_dragon_ok.xml"
        }
    ]

    spell_tests = [
        {
            "name": "Agitation (Sort rang 1 avec jets de sauvegarde)",
            "md": "./tests/fixtures/test_agitation.md",
            "xml": "./tests/fixtures/test_agitation_ok.xml"
        }
    ]

    all_passed = True
    for t in monster_tests:
        if not run_snapshot_test(t["name"], t["md"], t["xml"]):
            all_passed = False
    for t in spell_tests:
        if not run_snapshot_test_spells(t["name"], t["md"], t["xml"]):
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT AU VERT ! Tu peux continuer à coder sereinement.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ. Vérifie tes modifications (ou mets à jour tes Snapshots si le changement est voulu).")