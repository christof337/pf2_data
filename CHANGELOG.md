# CHANGELOG — historique des jalons

## 2026-04-08
- Fix Cat F : noms de sort sur 2 lignes (`**NOM\nSUITE**`) normalisés avant split (ex. CONVOCATION DE PLANTE OU DE CHAMPIGNON)
- Fix Intensifié convocation : `Intensifié. Comme indiqué sous le trait convocation` expansé en 9 entrées `<heighten>` explicites (2e→Niv.1 … 10e→Niv.15) et supprimé de la description
- Script one-liner `scripts/to_obsidian.sh <input.md> <output.md> <sort|monstre>`
- Fixtures sorts 01–10 régénérées depuis PDF (pages 316-391) avec chevauchement de page (dernière page de batch N = première de batch N+1)
- Golden batch 01 béni : `tests/fixtures/test_sorts_01_ok.xml` (51 sorts, pages 316-324)
- Golden batch 02 béni : `tests/fixtures/test_sorts_02_ok.xml` (51 sorts, pages 324-330)
- Previews Obsidian : `sorts_batch_01.md`, `sorts_batch_02.md`, `sorts_batch_03.md`

## 2026-04-07
- Support tableaux PDF → XML → Obsidian : `extract_pdf.py` injecte des marqueurs `[[TABLE_*]]`, `parse_table_markers()` dans `utils.py` les consomme, `spells_mapper.py` génère `<table>/<headerLine>/<line>/<cell>`, `spell_to_obsidian.xsl` les rend en tables Markdown, `spell.xsd` mis à jour avec `tableType` et `rowType`
- Champ `<trigger>` ajouté au XSD `spell.xsd` et au mapper
- Option `--pages X-Y` dans `extract_pdf.py`
- Corrections manuelles batch 01 : ALARME, BARRAGE DE FORCE, BULLE D'AIR, CHEMIN SÛR, TRANQUILISER

## 2026-04-01
- Refactoring Phase 2 : extraction de `utils.py`, nettoyage code mort, correction bug double-write batch, consolidation index loaders linker

## Avant 2026-04-01
- Pipeline monstres complet (extraction → XML → Obsidian) ; monstre de référence : **Jeune Dragon Empyréen**
- Infrastructure transversale : `xml_validator.py`, `slug_generator.py`, XSD pour monstres / sorts / traits / capacités
- Pipeline sorts : `spells_mapper.py`, `spell_to_obsidian.xsl`
- Pipeline traits : `trait_mapper.py` + `traits.xml`
- Pipeline capacités : `ability_mapper.py` + `abilities.xml`
- Post-processing cross-liens : `linker.py` (traits, sorts, capacités, spellRefs)
- Fusion XML : `merge_xml.py` (arbitrage par description, rapport de conflits)
