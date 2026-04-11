#!/usr/bin/env bash
# Usage: bash scripts/to_obsidian.sh <input.md> <output.md> <type>
#   type : sort | monstre | don
# Exemple :
#   bash scripts/to_obsidian.sh tests/fixtures/test_sorts_02.md obsidian_vault/preview/sorts_batch_02.md sort

set -e

INPUT="$1"
OUTPUT="$2"
TYPE="${3:-sort}"

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Usage: bash scripts/to_obsidian.sh <input.md> <output.md> <type=sort|monstre|don>"
    exit 1
fi

TMP_XML=$(mktemp /tmp/to_obsidian_XXXX.xml)
trap 'rm -f "$TMP_XML"' EXIT

case "$TYPE" in
    sort)
        MAPPER="scripts/spells_mapper.py"
        XSL="xslt/spell_to_obsidian.xsl"
        ;;
    monstre)
        MAPPER="scripts/monster_mapper.py"
        XSL="xslt/monster_to_obsidian.xsl"
        ;;
    don)
        MAPPER="scripts/feats_mapper.py"
        XSL="xslt/feat_to_obsidian.xsl"
        ;;
    *)
        echo "Type inconnu : '$TYPE'. Valeurs acceptées : sort, monstre, don"
        exit 1
        ;;
esac

echo "[1/2] Parsing $TYPE : $INPUT → $TMP_XML"
uv run "$MAPPER" "$INPUT" "$TMP_XML"

echo "[2/2] Transformation XSLT : $TMP_XML → $OUTPUT"
java -jar ~/lib/java/saxon-he-11.7.jar -s:"$TMP_XML" -xsl:"$XSL" -o:"$OUTPUT"

echo "Done : $OUTPUT"
