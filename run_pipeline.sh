#!/bin/bash

# --- CONFIGURATION DES CHEMINS ---
# On utilise des chemins relatifs au dossier du projet pour la portabilité
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
SAXON_JAR="/Users/slither/lib/java/saxon-he-11.7.jar"
RESOLVER_JAR="/Users/slither/lib/java/xmlresolver-4.2.0.jar"
SAXON_CP="$SAXON_JAR:$RESOLVER_JAR"

# --- VÉRIFICATION DE L'ENTRÉE ---
if [ -z "$1" ]; then
    echo "❌ Erreur : Aucun fichier PDF spécifié."
    echo "Usage :./run_pipeline.sh chemin/vers/monstre.pdf"
    exit 1
fi

PDF_INPUT="$1"
MD_LOCATION="$PROJECT_DIR/data/monsters"

echo "--- 🐉 DÉMARRAGE PIPELINE PATHFINDER 2E ---"

# Étape 1 : PDF -> Markdown Structuré
# Note : Assure-toi que extract_pdf.py prend sys.argv[1] comme entrée
echo "[1/3] Extraction géométrique (pdfplumber)..."
$VENV_PYTHON "$PROJECT_DIR/scripts/extract_pdf.py" "$PDF_INPUT" "$MD_LOCATION"
if [ $? -ne 0 ]; then echo "❌ Échec à l'étape 1"; exit 1; fi

# Étape 2 : Markdown -> XML Pivot
echo "[2/3] Mapping sémantique vers XML..."
$VENV_PYTHON "$PROJECT_DIR/scripts/xml_mapper.py"
if [ $? -ne 0 ]; then echo "❌ Échec à l'étape 2"; exit 1; fi

# Étape 3 : XML -> Obsidian (Saxon XSLT)
echo "[3/3] Transformation XSLT vers Obsidian..."
java -jar "$SAXON_JAR" -s:"$MD_LOCATION/JEUNE DRAGON EMPYRÉEN.xml" -xsl:"$PROJECT_DIR/xslt/monster_to_obsidian.xsl" -o:"$PROJECT_DIR/obsidian_vault/Bestiaire/JEUNE DRAGON EMPYRÉEN.md"
#java -cp "$SAXON_CP" net.sf.saxon.Transform \
#    -xsl:"$PROJECT_DIR/xslt/monster_to_obsidian.xsl" \
#    -s:"$PROJECT_DIR/data/unique.xml" \
#    -o:"$PROJECT_DIR/obsidian_vault/Bestiaire/log.txt"

if [ $? -eq 0 ]; then
    echo "--- ✅ PIPELINE TERMINÉE AVEC SUCCÈS ---"
    echo "La note a été générée dans obsidian_vault/Bestiaire/"
else
    echo "❌ Erreur lors de la transformation XSLT."
    exit 1
fi
