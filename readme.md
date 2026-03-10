# Pathfinder 2e : Corpus Master Français (Éditeur Officiel)

Ce projet vise à compiler l'intégralité du contenu technique de Pathfinder Seconde Édition à partir des PDF de l'Éditeur Officiel. L'objectif est de créer une base de données **XML** unique (Pivot) capable de générer des notes interconnectées pour **Obsidian** (Consultation) ou des documents de haute qualité via **LaTeX** (Prestige).

## 1. Choix Technologiques

* **Source of Truth :** PDF natifs de la version française (Éditeur Officiel).
* **Gestionnaire de paquets :** `uv` pour la rapidité et la résolution de dépendances complexes.
* **Extraction (Mac Intel) :** `pdfplumber` avec logique géométrique (détection de colonnes/encarts) pour pallier l'absence de support des modèles Deep Learning récents sur architecture x86_64.
* **Format Pivot :** **XML / XSD** pour garantir l'intégrité des données (typage fort) et permettre le "Single Source Publishing".
* **Moteur de Rendu :** **XSLT 3.0** (Saxon-HE) pour transformer l'arbre XML en Markdown structuré avec Frontmatter YAML.

## 2. Guide d'Installation (macOS Intel)

### Prérequis

* **Python 3.12** (installé via Homebrew).
* **Java JRE** (requis pour Saxon/XSLT).
* **Saxon-HE (JAR)** placé dans `~/lib/java/`.

### Installation du projet

```bash
# 1. Installer uv
brew install uv

# 2. Créer l'environnement virtuel avec la bonne version Python
uv venv --python 3.12
source .venv/bin/activate

# 3. Installer les librairies d'ingénierie de données
uv pip install pdfplumber lxml

```

## 3. Feuille de Route : De l'Extraction à l'Industrialisation

### Phase 1 : Le POC Transversal (Subset : 1 Monstre)

* ✅ Extraire une page complexe (ex: Dragon) avec encarts.
* Mapper vers un XML respectant le XSD "Monster".
* Générer une note Obsidian avec le plugin *Fantasy Statblocks*.

### Phase 2 : Industrialisation par Catégorie

* **Subset "Bestiaire" :** Traitement par lot d'un PDF complet. Ajout de la balise `<source_id>` (Livre, Page) dans chaque XML.
* **Subset "Équipement" :** Création du XSD "Item". Adaptation du script de mapping pour parser les tableaux de prix et de bulk.
* **Expansion :** Sorts, Dons, Dangers (Hazards), etc.

### Phase 3 : Agrégation Massive

* Fusion des index par catégories transversales (tous les objets magiques, peu importe le livre).
* Gestion des conflits Legacy/Remaster (Aliasing dans le XML).

## 4. Quickstart : Le Workflow de Travail

Pour traiter un nouveau document ou mettre à jour la base, suivez ces étapes dans **Visual Studio Code** :

### Étape 1 : PDF → Markdown Structuré

**Script :** `scripts/extract_pdf.py`

* **Action :** Analyse géométrique des `rects` pour isoler les sidebars du flux principal.
* **Output :** `output/temp/page_X_structured.md`.

### Étape 2 : Markdown → XML (Pivot)

**Script :** `scripts/step2_xml_mapper.py`

* **Action :** Utilise des Regex pour capturer les stats (CA, PV, Attributes) et les injecter dans l'arbre `lxml`.
* **Output :** `data/monsters/nom_du_monstre.xml`.

### Étape 3 : XML → Obsidian (Markdown)

**Outil :** XSLT (via le raccourci `Ctrl+Shift+B` configuré dans `tasks.json`).

* **Action :** Transformation de la donnée XML en fichier Markdown compatible Obsidian (YAML Frontmatter + Action Icons).
* **Output :** Votre coffre Obsidian `obsidian_vault/`.

---

**Note technique :** Sur une machine type Mac Silicon (M1/M2/M3), l'Étape 1 pourra être migrée vers **MinerU** pour une extraction sémantique encore plus fine via Deep Learning. Pour le moment, la méthode `pdfplumber` reste la plus stable sur le Mac Intel Ventura.