"""
batch_monster_mapper.py
Traitement en lot des monstres du Livre des Monstres PF2e.

Usage:
  uv run scripts/batch_monster_mapper.py [input_md] [output_dir] [log_file]

Entrée  : output/ldm_full/PF2R_03_Livre_des_monstres_web_v1.md
Sortie  : data/monsters/{slug}.xml pour chaque monstre
Log     : output/ldm_full/batch_report.log
"""

import io
import re
import os
import sys
import time
import traceback
from lxml import etree

# Import des fonctions du mapper existant
sys.path.insert(0, os.path.dirname(__file__))
from monster_mapper import parse_monster_md, generate_monster_xml
from slug_generator import generate_slug
from xml_validator import validate_xml

XSD_PATH = os.path.join(os.path.dirname(__file__), "..", "schema", "monster.xsd")

# ==========================================
# DÉCOUPAGE EN BLOCS DE MONSTRES
# ==========================================

# Pattern de détection d'un titre de monstre
# Exemple: **AIGLE GÉANT CRÉATURE 3  ou  AIGUILLONNEUR TOXIQUE CRÉATURE 9
MONSTER_TITLE_PATTERN = re.compile(
    r'^\s*\*{0,2}([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-\'\.0-9]{2,}?)\s+CRÉATURE\s+([\+\-−]?\s*\d+)',
    re.MULTILINE
)


def extract_monster_section(md_content):
    """
    Extrait la section Monstres A-Z (depuis PAGE 8 jusqu'au Glossaire des pouvoirs).
    Retourne (section_text, start_offset_in_original).
    """
    page8_match = re.search(r'\[\[PAGE 8\]\]', md_content)
    glossaire_match = re.search(r'GLOSSAIRE\s+DES\s+POUVOIRS', md_content)

    if not page8_match:
        print("[BATCH] ERREUR : marqueur [[PAGE 8]] non trouvé.")
        return None, 0

    start = page8_match.start()
    end = glossaire_match.start() if glossaire_match else len(md_content)
    return md_content[start:end], start


def split_into_monster_blocks(section_text):
    """
    Découpe la section monstres en blocs individuels.
    Retourne une liste de (name, level, raw_block_text).

    Stratégie : on repère chaque titre CRÉATURE N, et le bloc d'un monstre
    s'étend du titre courant jusqu'au titre suivant.
    """
    matches = list(MONSTER_TITLE_PATTERN.finditer(section_text))
    print(f"[BATCH] {len(matches)} titres de monstres détectés dans le MD.")

    blocks = []
    for i, m in enumerate(matches):
        name_raw = m.group(1).strip().rstrip('*').strip()
        level_raw = m.group(2).strip().replace('−', '-').replace('–', '-')

        # Bloc : depuis le début du titre jusqu'au titre suivant (ou fin)
        block_start = m.start()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        raw_block = section_text[block_start:block_end]

        blocks.append({
            'name': name_raw,
            'level': level_raw,
            'text': raw_block,
            'match_pos': m.start(),
        })

    return blocks


def build_parseable_md(monster_block):
    """
    Construit un mini-MD que parse_monster_md() peut ingérer.
    Le parser attend : [[PAGE 1]] puis # FLUX PRINCIPAL (STATS/BASE) puis le contenu.
    """
    return f"[[PAGE 1]]\n\n# FLUX PRINCIPAL (STATS/BASE)\n{monster_block['text']}\n"


# ==========================================
# TRAITEMENT EN LOT
# ==========================================

def process_monsters_batch(md_content, output_dir, log_path):
    """
    Traite en lot tous les monstres du MD.
    Retourne (nb_success, nb_errors).
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    section_text, _ = extract_monster_section(md_content)
    if section_text is None:
        return 0, 0

    blocks = split_into_monster_blocks(section_text)

    nb_success = 0
    nb_errors = 0
    nb_xsd_errors = 0
    errors = []

    log_lines = [
        f"=== Batch Monster Mapper — {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n",
        f"Total monstres détectés : {len(blocks)}\n",
        "-" * 60 + "\n",
    ]

    for idx, block in enumerate(blocks, 1):
        name = block['name']
        slug = generate_slug('monster', name)
        output_file = os.path.join(output_dir, f"{slug}.xml")

        print(f"[BATCH] [{idx}/{len(blocks)}] {name}...", end=' ', flush=True)

        try:
            mini_md = build_parseable_md(block)

            # Silencer les print() verbeux du parser et du générateur XML
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                monster_data = parse_monster_md(mini_md)
            finally:
                sys.stdout = old_stdout

            # Vérifications minimales
            if not monster_data.get('name'):
                raise ValueError("Nom du monstre non extrait")
            if not monster_data.get('level'):
                raise ValueError("Niveau du monstre non extrait")

            # Silencer la sortie verbeuse de generate_monster_xml
            sys.stdout = io.StringIO()
            try:
                generate_monster_xml(monster_data, output_file)
            finally:
                sys.stdout = old_stdout

            # Validation XSD (silencieux pour ne pas noyer les logs batch)
            xsd_ok = validate_xml(output_file, XSD_PATH, silent=True)
            if not xsd_ok:
                nb_xsd_errors += 1
                print(f"XSD KO -> {slug}.xml")
                log_lines.append(f"[XSD]   {idx:>4}. {name} -> {slug}.xml\n")
            else:
                nb_success += 1
                print(f"OK -> {slug}.xml")
                log_lines.append(f"[OK]    {idx:>4}. {name} -> {slug}.xml\n")

        except Exception as e:
            nb_errors += 1
            err_msg = str(e)
            tb = traceback.format_exc()
            print(f"ERREUR : {err_msg}")
            log_lines.append(f"[ERR]   {idx:>4}. {name} | {err_msg}\n")
            errors.append({'name': name, 'error': err_msg, 'traceback': tb})

    # Écriture du log
    log_lines.append("\n" + "=" * 60 + "\n")
    log_lines.append(f"RÉSUMÉ : {nb_success} succès, {nb_xsd_errors} invalides XSD, {nb_errors} erreurs\n")

    if errors:
        log_lines.append("\nDÉTAIL DES ERREURS :\n")
        for err in errors:
            log_lines.append(f"\n  Monstre : {err['name']}\n")
            log_lines.append(f"  Erreur  : {err['error']}\n")
            log_lines.append(f"  Traceback:\n")
            for line in err['traceback'].split('\n'):
                log_lines.append(f"    {line}\n")

    with open(log_path, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)

    print(f"\n[BATCH] === RÉSUMÉ ===")
    print(f"[BATCH] Succès       : {nb_success}")
    print(f"[BATCH] Invalides XSD: {nb_xsd_errors}")
    print(f"[BATCH] Erreurs      : {nb_errors}")
    print(f"[BATCH] Log          : {log_path}")

    return nb_success, nb_xsd_errors, nb_errors


# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/ldm_full/PF2R_03_Livre_des_monstres_web_v1.md"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/monsters"
    log_file = sys.argv[3] if len(sys.argv) > 3 else "output/ldm_full/batch_report.log"

    if not os.path.exists(input_file):
        print(f"[BATCH] ERREUR : fichier introuvable : {input_file}")
        sys.exit(1)

    print(f"[BATCH] Lecture de {input_file}...")
    start_total = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    print(f"[BATCH] Fichier chargé ({len(md_content)} caractères)\n")

    nb_ok, nb_xsd, nb_err = process_monsters_batch(md_content, output_dir, log_file)

    elapsed = time.time() - start_total
    print(f"\n[BATCH] Temps total : {elapsed:.1f}s")
    print(f"[BATCH] Terminé.")
