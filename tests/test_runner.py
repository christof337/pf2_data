import os
import difflib
import tempfile
import sys

sys.path.append(os.path.relpath("scripts"))

from monster_mapper import parse_monster_md, generate_monster_xml
from spells_mapper import parse_spells_md, generate_spells_xml
from trait_mapper import parse_traits_md, generate_trait_xml
from xml_validator import validate_xml

def run_snapshot_test(name, md_path, expected_xml_path, parse_fn, generate_fn, xsd_path=None):
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

        # 3. Comparaison snapshot
        if actual_xml != expected_xml:
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

        # 4. Validation XSD (si schéma fourni) — le fichier temporaire existe encore ici
        if xsd_path:
            if not validate_xml(temp_output, xsd_path):
                print(f"  ❌ ÉCHEC XSD : le XML généré ne valide pas {xsd_path}\n")
                return False

    print(f"  ✅ SUCCÈS : Le XML généré est identique au Snapshot.\n")
    return True

if __name__ == "__main__":
    print("="*50)
    print("LANCEMENT DES TESTS DE NON-RÉGRESSION")
    print("="*50)

    tests = [
        {
            "name": "Jeune Dragon Empyréen (Monstre Standard)",
            "md":  "./tests/fixtures/test_dragon.md",
            "xml": "./tests/fixtures/test_dragon_ok.xml",
            "xsd": "./schema/monster.xsd",
            "parse":    parse_monster_md,
            "generate": generate_monster_xml,
        },
        {
            "name": "Sorts LdJ (468 sorts)",
            "md":  "./tests/fixtures/test_sorts.md",
            "xml": "./tests/fixtures/test_sorts_ok.xml",
            "xsd": "./schema/spell.xsd",
            "parse":    parse_spells_md,
            "generate": generate_spells_xml,
        },
        {
            "name": "Traits LdM (format §**Nom.** description)",
            "md":  "./tests/fixtures/test_traits.md",
            "xml": "./tests/fixtures/test_traits_ok.xml",
            "xsd": "./schema/trait.xsd",
            "parse":    parse_traits_md,
            "generate": generate_trait_xml,
        },
        {
            "name": "Traits LdJ (format **Nom** (trait). — 9 cas edge)",
            "md":  "./tests/fixtures/test_traits_ldj.md",
            "xml": "./tests/fixtures/test_traits_ldj_ok.xml",
            "xsd": "./schema/trait.xsd",
            "parse":    lambda content: parse_traits_md(content, format="ldj"),
            "generate": generate_trait_xml,
        },
    ]

    all_passed = True
    for t in tests:
        if not run_snapshot_test(
            t["name"], t["md"], t["xml"],
            t["parse"], t["generate"],
            xsd_path=t.get("xsd")
        ):
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT AU VERT ! Tu peux continuer à coder sereinement.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ. Vérifie tes modifications (ou mets à jour tes Snapshots si le changement est voulu).")
