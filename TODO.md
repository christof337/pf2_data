# TODO — tâches en cours

## État actuel
- Validation du preview batch 01 en attente de bénédiction du golden `tests/fixtures/test_sorts_01_ok.xml`
- Le pipeline sorts est fonctionnel, mais les batches 02–10 restent à valider progressivement
- Le support des tableaux PDF est en place, mais mérite encore des vérifications sur des cas réels
- Les champs mécaniques `<cost>` et `<requirements>` restent à implémenter proprement

## Jalons récents déjà accomplis
- Pipeline monstres complet (extraction → XML → Obsidian) ; monstre de référence : **Jeune Dragon Empyréen**
- Infrastructure transversale : `xml_validator.py`, `slug_generator.py`, XSD pour monstres / sorts / traits / capacités
- Pipeline sorts : `spells_mapper.py` fonctionnel, `all_spells.xml` peuplé, `spell_to_obsidian.xsl` présent
- Pipeline traits : `trait_mapper.py` + `traits.xml`
- Pipeline capacités : `ability_mapper.py` + `abilities.xml`
- Post-processing cross-liens : `linker.py` (traits, sorts, capacités, spellRefs)
- Fusion XML : `merge_xml.py` (arbitrage par description, rapport de conflits)
- Refactoring Phase 2 (2026-04-01) : extraction de `utils.py`, nettoyage code mort, correction bug double-write batch, consolidation index loaders linker
- Support tableaux PDF → XML → Obsidian (2026-04-07) : `extract_pdf.py` injecte des marqueurs `[[TABLE_*]]`, `parse_table_markers()` dans `utils.py` les consomme, `spells_mapper.py` génère `<table>/<headerLine>/<line>/<cell>`, `spell_to_obsidian.xsl` les rend en tables Markdown, `spell.xsd` mis à jour avec `tableType` et `rowType`
- Option `--pages X-Y` ajoutée à `extract_pdf.py` pour extraire seulement un sous-ensemble de pages
- Champ `<trigger>` ajouté au XSD `spell.xsd` et au mapper (détection case-sensitive de `**Déclencheur` en début de ligne mécanique)
- Corrections batch 01 (2026-04-07) : ALARME, BARRAGE DE FORCE, BULLE D'AIR, CHEMIN SÛR, TRANQUILISER
- Preview batch 01 : `obsidian_vault/preview/sorts_batch_01.md` contient 51 sorts (46 du batch + 5 débordant sur la page 324)

## Priorité haute
- [ ] valider le batch sorts 01
- [ ] bénir officiellement `tests/fixtures/test_sorts_01_ok.xml` si la sortie est validée
- [ ] finaliser l’ajout de `<cost>` au schéma, au mapper et au XSL
- [ ] finaliser l’ajout de `<requirements>` au schéma, au mapper et au XSL

## Priorité moyenne
- [ ] valider et bénir progressivement les batches sorts 02–10
- [ ] vérifier les sorties Obsidian générées pour les sorts
- [ ] reprendre le traitement par lot du Bestiaire complet
- [ ] traiter les autres familles de données restantes : équipement, dons, dangers

## Points de travail immédiatement utiles
- [ ] poursuivre les tests de parsing sur les tableaux PDF
- [ ] surveiller les cas de sorts coupés en fin de page
- [ ] garder une trace des corrections ponctuelles dans le code, pas dans ce fichier
