# CLAUDE.md — Pathfinder 2e : Corpus Master Français

## Objectif du projet

Compiler l'intégralité du contenu technique de **Pathfinder 2e (version française, Éditeur Officiel)** depuis les PDFs sources, et construire :

1. **Une base XML structurée et validée** (source of truth unique)
2. **Des notes Obsidian** générées via XSLT (pour consultation en jeu / préparation)
3. **À terme : un site web de référence en français**, inspiré d'[Archives of Nethys (aonprd.com)](https://2e.aonprd.com/) mais pour la VF — avec navigation interconnectée : cliquer sur un trait renvoie vers sa définition et tous les éléments qui le portent ; cliquer sur une source liste tous ses éléments ; liens bidirectionnels entre sorts, monstres, dons, etc.

---

## Stack technique

| Rôle | Outil |
|---|---|
| Extraction PDF | `pdfplumber` (logique géométrique, compatible Mac Intel x86_64) |
| Gestion deps | `uv` + Python 3.12 |
| Format pivot | XML + XSD (validation forte via `lxml`) |
| Transformation | XSLT (Saxon-HE JAR dans `~/lib/java/`) |
| Validation | `scripts/xml_validator.py` |
| Slugs / IDs | `scripts/slug_generator.py` (normalisation ASCII, préfixe par type) |
| Sortie actuelle | Markdown Obsidian (`obsidian_vault/`) |
| Sortie future | Site web (technologie non encore choisie) |

**Note Mac Intel :** `pdfplumber` avec détection géométrique de colonnes/encarts est le choix stable sur x86_64. Sur Mac Silicon, la migration vers MinerU (Deep Learning) sera envisageable.

---

## Architecture des données

```
pdf_sources/          → PDFs originaux (source of truth physique) [gitignored]
scripts/              → Pipeline Python (extraction, mapping, validation)
  extract_pdf.py      → PDF → Markdown brut structuré
  monster_mapper.py   → Markdown → XML monstres
  spells_mapper.py    → Markdown → XML sorts
  trait_mapper.py     → Markdown → XML traits
  ability_mapper.py   → Markdown → XML capacités universelles
  batch_monster_mapper.py → Traitement en lot du Bestiaire complet
  linker.py           → Post-processing : ajout des ref= croisés (traits/sorts/capacités)
  merge_xml.py        → Fusion de fichiers XML par attribut id
  utils.py            → Utilitaires partagés (clean_text, parse_table_markers, split_bullet_list)
  xml_validator.py    → Validation XSD
  slug_generator.py   → Génération d'IDs normalisés
  old/                → Anciens scripts (archivés, ne pas modifier)
schema/               → Schémas XSD (monster.xsd, spell.xsd, trait.xsd, ability.xsd)
xslt/                 → Transformations XSLT uniquement
  monster_to_obsidian.xsl
  spell_to_obsidian.xsl
  decodeMonster.xsl
  old/                → Anciennes transformations (archivées)
data/
  monsters/           → XMLs monstres individuels
  spells/             → all_spells.xml (fichier agrégé)
  traits/             → traits.xml
output/               → Fichiers intermédiaires de travail (temporaires) [gitignored]
obsidian_vault/       → Notes Obsidian générées [gitignored sauf preview/]
  preview/            → Quelques exemples trackés manuellement
tests/
  fixtures/           → Inputs MD + golden XML de référence [ZONE PROTÉGÉE]
  test_runner.py      → Runner de non-régression [ZONE PROTÉGÉE]
```

---

## Schéma XML : conventions clés

- **IDs** : format `{type}-{slug}` (ex: `spell-agitation`, `trait-mental`, `monster-jeune-dragon-empyreen`)
- **`<type>`** : élément avec attribut `type` (ex: `<type type="spell"/>` ou `<type type="cantrip"/>`) — c'est intentionnel selon le XSD
- **`<richTextType>`** : nœuds mixtes (texte + `<spellRef>`) pour les descriptions avec références croisées inline
- **Traditions** : enum stricte dans le XSD — `arcanique`, `occulte`, `primordiale`, `divine`
- **Traits multi-mots** : liste explicite dans `spells_mapper.py` (`NON LÉTAL`, `PEU COURANT`, etc.)

---

## État d'avancement (Phase 2 en cours)

### Terminé
- Pipeline monstres complet (extraction → XML → Obsidian). Monstre de référence : **Jeune Dragon Empyréen**.
- Infrastructure transversale : `xml_validator.py`, `slug_generator.py`, XSD pour monstres/sorts/traits/capacités.
- Pipeline sorts : `spells_mapper.py` fonctionnel, `all_spells.xml` peuplé, `spell_to_obsidian.xsl` présent.
- Pipeline traits : `trait_mapper.py` + `traits.xml`.
- Pipeline capacités : `ability_mapper.py` + `abilities.xml`.
- Post-processing cross-liens : `linker.py` (traits, sorts, capacités, spellRefs).
- Fusion XML : `merge_xml.py` (arbitrage par description, rapport de conflits).
- **Refactoring Phase 2** (2026-04-01) : extraction de `utils.py`, nettoyage code mort, correction bug double-write batch, consolidation index loaders linker.
- **Support tableaux PDF → XML → Obsidian** (2026-04-07) : `extract_pdf.py` injecte des marqueurs `[[TABLE_*]]`, `parse_table_markers()` dans `utils.py` les consomme, `spells_mapper.py` génère `<table>/<headerLine>/<line>/<cell>`, `spell_to_obsidian.xsl` les rend en tables Markdown. XSD `spell.xsd` mis à jour avec `tableType` et `rowType`.
- **Option `--pages X-Y`** ajoutée à `extract_pdf.py` : permet d'extraire seulement un sous-ensemble de pages (évite les ~5 min de traitement du PDF entier). Les pages sont 1-indexées dans l'argument, 0-indexées en interne.
- **Champ `<trigger>`** ajouté au XSD `spell.xsd` et au mapper (détection case-sensitive de `**Déclencheur` en début de ligne mécanique, distincte du mot "déclencheur" dans le texte narratif).
- **Corrections batch 01** (2026-04-07) : ALARME (fausse réaction), BARRAGE DE FORCE (intensifié type `2e`→`+2`, override hardcodé dans le mapper), BULLE D'AIR (déclencheur non capturé), CHEMIN SÛR (artefact `**` en fin de description), TRANQUILISER (sauvegardes perdues car Cat-E callout coupé par `[[PAGE N]]`).
- **Preview batch 01** : `obsidian_vault/preview/sorts_batch_01.md` contient 51 sorts (46 du batch + 5 débordant sur la page 324). CHANT ÉNIGMATIQUE affiche son tableau Markdown correctement.

### En cours
- Validation du preview batch 01 par l'utilisateur → bénédiction du golden `tests/fixtures/test_sorts_01_ok.xml`.
- Champs manquants à ajouter au mapper/XSD : `<cost>` (Coût) et `<requirements>` (Conditions) — présents dans le LdJ (ex. RAPPEL À LA VIE pour Coût, ENFERMER L'ÂME pour Conditions). `Locus` absent du LdJ, à surveiller dans les autres livres.

### À faire
- `spell_to_obsidian.xsl` : vérifier compatibilité XSLT 1.0 vs Saxon 3.0.
- Valider et bénir les batches 02–10 progressivement.
- Traitement par lot (Bestiaire complet, puis autres livres).
- Ajout de `<source_id>` (livre + page) dans chaque entité XML.
- Subset Équipement (XSD Item, parsing tableaux bulk/prix).
- Dons, Dangers (Hazards).
- Phase 3 : agrégation cross-livres, gestion conflits Legacy/Remaster.

---

## Stratégie de test — règles non négociables

Le projet utilise du **golden master testing** (snapshot testing) : chaque mapper est testé en comparant sa sortie XML contre un fichier de référence validé manuellement par le propriétaire du projet.

### Règles pour Claude

**`tests/` est une zone protégée.** Ne jamais modifier :
- `tests/fixtures/*.md` — inputs de référence
- `tests/fixtures/*_ok.xml` ou tout fichier XML de référence — golden masters
- `tests/test_runner.py` — le runner lui-même

La seule exception est un refactoring structurel explicitement demandé par l'utilisateur.

**Avant tout commit touchant un mapper ou une regex :**
```bash
python tests/test_runner.py
```
Si un test échoue → **s'arrêter, signaler la régression à l'utilisateur, ne pas continuer**. Ne jamais régénérer un golden master pour "faire passer" un test — ce serait exactement contourner le système.

**Seul l'utilisateur peut bénir un nouveau golden master.** Si une amélioration change légitimement la sortie XML, c'est lui qui valide le nouveau fichier de référence et le commite.

### Logique du runner

`test_runner.py` fait, pour chaque test :
1. input MD → `parse_*()` → `generate_*_xml()` dans un fichier temporaire
2. Comparaison stricte caractère par caractère avec le golden XML
3. Validation XSD du fichier généré contre le schéma correspondant (`monster.xsd`, `spell.xsd`, `trait.xsd`)

La comparaison est intentionnellement stricte : tout écart, même cosmétique, est une régression. La validation XSD garantit qu'un changement de schéma qui invaliderait un golden master existant est détecté immédiatement.

### Périmètre actuel des tests

- Monstres : `test_dragon.md` / `test_dragon_ok.xml` (Jeune Dragon Empyréen)
- Sorts : 10 batches progressifs (voir ci-dessous)
- Traits LdM : `test_traits.md` / `test_traits_ok.xml` (~400 traits format LdM)
- Traits LdJ : `test_traits_ldj.md` / `test_traits_ldj_ok.xml` (153 traits format LdJ)

### Batches progressifs — sorts LdJ

Les 471 sorts sont découpés en 10 batches (`test_sorts_01.md` … `test_sorts_10.md`, ~46 sorts chacun).
Le runner auto-découvre les goldens validés (`test_sorts_NN_ok.xml`) : un fichier absent = batch pas encore béni = pas testé.

**Workflow pour valider un nouveau batch :**
1. Générer : `uv run scripts/spells_mapper.py tests/fixtures/test_sorts_NN.md output/golden_work/spells_ldj_batch_NN.xml`
2. Inspecter le XML (0 INCONNU, 0 `*` résiduels, traditions correctes)
3. Si OK, bénir : `cp output/golden_work/spells_ldj_batch_NN.xml tests/fixtures/test_sorts_NN_ok.xml`
4. Lancer les tests : `uv run tests/test_runner.py` — tous les batches déjà bénis doivent passer

**Règle absolue :** seul l'utilisateur bénit un golden. Claude ne copie jamais vers `tests/fixtures/` sans validation explicite.

---

## Points de vigilance

- **`spell_to_obsidian.xsl` est en XSLT 1.0** alors que le README annonce Saxon (XSLT 3.0). Fonctionne en dégradé, mais ne profite pas des fonctionnalités 3.0.
- **`scripts/old/`** : à archiver ou supprimer quand les mappers courants sont stabilisés.
- Les **IDs XML sont des `xs:ID`** : unicité garantie par le XSD, mais le slug doit être stable entre les runs (actuellement basé sur le nom, pas sur un identifiant canonique PF2e).
- **Corrections d'erreurs PDF hardcodées dans le mapper** : BARRAGE DE FORCE a une entrée intensifiée erronée dans le PDF (`Intensifié 2e` au lieu de `Intensifié +2`). Le mapper corrige ça via un override post-parsing ciblant le nom du sort. C'est une stratégie à formaliser : les corrections PDF doivent être explicitement documentées dans le code (commentaire + nom du sort) plutôt que noyées dans la logique générale.
- **Sorts en fin de page** : les sorts dont le statblock est coupé par un saut de page sont les plus sujets aux problèmes de parsing (sauvegardes tronquées, description incomplète). Pour le batch 01, les sorts à risque identifiés étaient : TRANQUILISER, ATTACHE PLANAIRE, AVATAR, BOURRASQUE, CATACLYSME, CHEMIN SÛR.

---

## Backlog — Known issues (à traiter plus tard, ne pas toucher sans instruction explicite)

Ces problèmes sont **identifiés et documentés**, mais délibérément différés. Ne pas les corriger de manière proactive.

### ⚠️ Purger les PDFs sources de l'historique git — PRIORITÉ SÉCURITÉ

Le dépôt est **public**. Des PDFs sources (livres de règles sous licence) ont été commités par le passé et sont toujours accessibles dans l'historique git même s'ils sont gitignorés aujourd'hui. Il faut les supprimer de l'intégralité de l'historique via `git filter-repo` (ou BFG Repo Cleaner), puis force-pusher. Opération destructive et irréversible — à planifier soigneusement, avec un backup local beforehand, et en coordination avec tous les contributeurs éventuels.

Commande de référence (à adapter) :
```bash
git filter-repo --path pdf_sources/ --invert-paths
# puis : git push --force --all
```

### "d'" dans les types de dégâts
Dans les frappes des monstres, on voit 
```
<damage>
            <amount>1d8</amount>
            <damageType>d’esprit</damageType>
          </damage>
```
j'aimerais voir apparaître "esprit" dans le damage type (plutôt que "d'esprit"), mais j'ai besoin que le xsl obsidian soit malin et ajoute tout seul "de" ou "d'" lorsque nécessaire.

### Sorts à actions variables
Certains sorts (guérison typiquement ou guérison de compagnon) donnent une "fourchette" d'actions à dépenser, entre 1 et 3, ou entre 2 et 3, parfois 2 ou plus. Il faudrait pouvoir gérer ça proprement en xml, pour permettre un maximum de combinaisons

### Caractères étranges slugifiés
~~le slug de mauvais œil c'est "sort-mauvais-il"~~ — **corrigé** : `slug_generator.py` remplace désormais `œ→oe`, `Œ→OE`, `æ→ae`, `Æ→AE` avant la normalisation NFKD.

### battleFormType (Avatar et formes de bataille)
Le sort _Avatar_ (et futurs sorts de forme) contient des blocs de stats de forme de combat qui ne rentrent pas dans la structure `<spell>` standard. Pour l'instant les `*` résiduels de ces blocs sont tolérés dans le golden. À terme : modéliser un `battleFormType` en XSD pour structurer proprement ces blocs.

### Sorts — Pipeline XML → Obsidian

1. **Superscript "e" dans les entrées intensifiées** (`spell_to_obsidian.xsl`)
   Les entrées de type `Intensifié (4e)` devraient afficher le "e" en exposant. Actuellement rendu en texte plat. Correction à apporter dans le XSLT.

2. **Sauts de ligne non préservés** (`spells_mapper.py` + `spell_to_obsidian.xsl`)
   Les descriptions sont aplaties en un seul bloc de texte. La mise en page originale du PDF (listes, paragraphes distincts) est perdue. À corriger dans le parsing et/ou le rendu XSLT.

3. **⚠️ Bug parsing — texte post-bloc SCSEEC perdu** (`spells_mapper.py`) — *plus grave*
   Si une description contient du texte **après** le bloc Succès critique / Succès / Échec / Échec critique, ce texte n'est pas capturé dans un champ dédié : il se retrouve accolé à la dernière entrée du bloc (typiquement `<criticalFailure>`). Correction à apporter dans la logique de délimitation de `parse_spell_block()`, probablement en ajoutant un champ `descriptionPost` ou en revoyant les bornes des regex de sauvegardes.

4. dans mysteres divins, on a eu un paquet de nouveaux statblocks pour le sort avatar. il faudrait en faire un xml à part enrichi de différentes sources (je pense)

5. les traits de rareté doivent apparaître en premier (puis par ordre alphabétique)

### Prochain type de données à intégrer

5. **Actions nommées** (Se cacher, Saisir, Se mettre à l'abri, Faire un pas, Aider, Chercher, Intimider, etc.)
   Ce sont les actions génériques disponibles à toutes les créatures. Elles apparaissent dans le LdJ (chapitre Actions). Nécessitera : un nouveau XSD (`action.xsd`), un `action_mapper.py`, et un `actions.xml` agrégé. Les monstres et sorts y font parfois référence → le linker devra être étendu.

### Architecture données — Questions ouvertes

4. **Pourquoi les monstres sont-ils en fichiers individuels alors que les sorts sont dans un seul fichier ?**
   Les sorts sont dans `data/spells/all_spells.xml` (fichier agrégé). Les monstres sont dans `data/monsters/*.xml` (un fichier par monstre). Cette asymétrie mérite d'être questionnée : un `all_monsters.xml` faciliterait les requêtes cross-bestiaire et serait cohérent avec l'approche sorts/traits. Le `batch_monster_mapper.py` devrait probablement générer un seul XML agrégé. À décider avant d'ajouter d'autres sources de monstres.

---

## Objectif site web (horizon Phase 3+)

Le site cible est fonctionnellement équivalent à [Archives of Nethys](https://2e.aonprd.com/) mais en français :
- Navigation croisée : trait → définition + tous les éléments portant ce trait
- Source → liste de tous les éléments de ce livre/page
- Recherche full-text sur les descriptions
- Le XML structuré est conçu dès maintenant pour supporter ces liens (IDs stables, `<spellRef>`, `<source_id>` à venir)
- Technologie frontend à choisir au moment de la Phase 3 (le XML pivot permettra de générer JSON/HTML/autre sans retoucher les données)

## erreurs à corriger asap

*Aucune correction urgente en attente au 2026-04-07 — les 5 bugs du batch 01 ont été résolus.*

### Champs mécaniques manquants (à implémenter prochainement)

- **`<cost>` (Coût)** : certains sorts ont une entrée `**Coût**` distincte (ex. RAPPEL À LA VIE, rituels). Actuellement absorbé dans `<cast>` s'il est inline, silencieusement perdu s'il est sur une ligne séparée. Ajouter au XSD, mapper et XSL.
- **`<requirements>` (Conditions)** : certains sorts ont une entrée `**Conditions**` distincte (ex. ENFERMER L'ÂME). Non capturé actuellement. Ajouter au XSD, mapper et XSL.
- **`Locus`** : absent du LdJ. À surveiller dans les autres livres (sorts de focus des mystères, etc.).
