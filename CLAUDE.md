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
  xml_validator.py    → Validation XSD
  slug_generator.py   → Génération d'IDs normalisés
  old/                → Anciens scripts (archivés, ne pas modifier)
schema/               → Schémas XSD (monster.xsd, spell.xsd, trait.xsd)
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
- Infrastructure transversale : `xml_validator.py`, `slug_generator.py`, XSD pour monstres/sorts/traits.
- Pipeline sorts : `spells_mapper.py` fonctionnel, `all_spells.xml` peuplé, `spell_to_obsidian.xsl` présent.
- Pipeline traits : `trait_mapper.py` + `traits.xml`.

### En cours
- Itération sur `spells_mapper.py` et `all_spells.xml` (fichiers modifiés non commités).
- Génération des notes Obsidian pour les sorts (`obsidian_vault/Sorts/`).

### À faire
- `spell_to_obsidian.xsl` : vérifier compatibilité XSLT 1.0 vs Saxon 3.0.
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

`test_runner.py` fait : input MD → `parse_*()` → `generate_*_xml()` dans un fichier temporaire → comparaison stricte caractère par caractère avec le golden XML. La comparaison est intentionnellement stricte : tout écart, même cosmétique, est une régression jusqu'à preuve du contraire.

### Périmètre actuel des tests

- Monstres : `test_dragon.md` / `test_dragon_ok.xml` (Jeune Dragon Empyréen)
- Sorts et traits : pas encore couverts — à enrichir progressivement par l'utilisateur

---

## Points de vigilance

- **`spell_to_obsidian.xsl` est en XSLT 1.0** alors que le README annonce Saxon (XSLT 3.0). Fonctionne en dégradé, mais ne profite pas des fonctionnalités 3.0.
- **`scripts/old/`** : à archiver ou supprimer quand les mappers courants sont stabilisés.
- Les **IDs XML sont des `xs:ID`** : unicité garantie par le XSD, mais le slug doit être stable entre les runs (actuellement basé sur le nom, pas sur un identifiant canonique PF2e).

---

## Backlog — Known issues (à traiter plus tard, ne pas toucher sans instruction explicite)

Ces problèmes sont **identifiés et documentés**, mais délibérément différés. Ne pas les corriger de manière proactive.

### Sorts — Pipeline XML → Obsidian

1. **Superscript "e" dans les entrées intensifiées** (`spell_to_obsidian.xsl`)
   Les entrées de type `Intensifié (4e)` devraient afficher le "e" en exposant. Actuellement rendu en texte plat. Correction à apporter dans le XSLT.

2. **Sauts de ligne non préservés** (`spells_mapper.py` + `spell_to_obsidian.xsl`)
   Les descriptions sont aplaties en un seul bloc de texte. La mise en page originale du PDF (listes, paragraphes distincts) est perdue. À corriger dans le parsing et/ou le rendu XSLT.

3. **⚠️ Bug parsing — texte post-bloc SCSEEC perdu** (`spells_mapper.py`) — *plus grave*
   Si une description contient du texte **après** le bloc Succès critique / Succès / Échec / Échec critique, ce texte n'est pas capturé dans un champ dédié : il se retrouve accolé à la dernière entrée du bloc (typiquement `<criticalFailure>`). Correction à apporter dans la logique de délimitation de `parse_spell_block()`, probablement en ajoutant un champ `descriptionPost` ou en revoyant les bornes des regex de sauvegardes.

---

## Objectif site web (horizon Phase 3+)

Le site cible est fonctionnellement équivalent à [Archives of Nethys](https://2e.aonprd.com/) mais en français :
- Navigation croisée : trait → définition + tous les éléments portant ce trait
- Source → liste de tous les éléments de ce livre/page
- Recherche full-text sur les descriptions
- Le XML structuré est conçu dès maintenant pour supporter ces liens (IDs stables, `<spellRef>`, `<source_id>` à venir)
- Technologie frontend à choisir au moment de la Phase 3 (le XML pivot permettra de générer JSON/HTML/autre sans retoucher les données)
