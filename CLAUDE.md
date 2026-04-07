# CLAUDE.md — Pathfinder 2e : Corpus Master Français

## Rôle du projet
Transformer les PDFs sources Pathfinder 2e VF en données structurées et validées, puis en sorties exploitables pour consultation et préparation.

Chaîne cible :
PDF → extraction → XML pivot validé → transformation Obsidian → extension future vers site web.

---

## Principes de travail

- Priorité à la stabilité du schéma et des sorties de référence.
- Ne pas élargir inutilement le périmètre d’une tâche.
- Ne pas explorer le repo au-delà du nécessaire.
- Préférer les corrections locales, explicites et traçables.
- Quand un point n’est pas demandé, ne pas le traiter “au passage”.

---

## Architecture de haut niveau

### Outils principaux
- Extraction PDF : `pdfplumber`
- Gestion des dépendances : `uv` + Python 3.12
- Validation : `lxml` + XSD
- Transformation : XSLT
- Génération d’IDs : `scripts/slug_generator.py`

### Flux de travail
- `scripts/` : extraction, mapping, fusion, validation
- `schema/` : schémas XSD
- `xslt/` : transformation vers Obsidian
- `data/` : XML généré
- `obsidian_vault/` : notes générées
- `tests/` : fixtures et golden masters

---

## Conventions XML à respecter

- IDs au format `{type}-{slug}`
- `<richTextType>` pour le texte mixte avec références croisées
- traditions strictes : `arcanique`, `occulte`, `primordiale`, `divine`
- les traits multi-mots sont gérés explicitement dans les mappers
- les IDs XML doivent rester stables entre les runs

---

## Règles de validation

### Zone protégée
`tests/` est une zone protégée.

Ne jamais modifier sans validation explicite :
- `tests/fixtures/*.md`
- `tests/fixtures/*_ok.xml`
- `tests/test_runner.py`

### Avant toute modification sur un mapper ou une regex
Lancer :
```bash
uv run tests/test_runner.py
```

Si un test échoue :
- s’arrêter
- signaler la régression
- ne pas régénérer un golden master sans validation explicite de l’utilisateur

---

## Fichiers de pilotage à consulter selon le besoin

### `TODO.md`
À consulter pour les tâches en cours et la priorité immédiate.
Utilisation pertinente quand la demande concerne :
- ce qu’on fait maintenant
- le prochain ticket à traiter
- l’ordre de traitement à court terme

### `BACKLOG.md`
À consulter pour la dette technique, les bugs connus, les idées différées et les questions ouvertes.
Utilisation pertinente quand la demande concerne :
- un problème déjà identifié mais non urgent
- une discussion d’architecture
- une décision à arbitrer plus tard

### `MODE_PARSING.md`
À consulter pour tout ce qui touche à l’extraction PDF, aux tableaux, aux heuristiques de parsing, et aux cas limites de lecture.
Utilisation pertinente quand la demande concerne :
- tableaux PDF
- découpe de pages
- marqueurs d’extraction
- faux positifs / faux négatifs de parsing

### `MODE_MAPPING.md`
À consulter si présent, pour les règles de transformation Markdown → XML et les conventions de mappers.
Utilisation pertinente quand la demande concerne :
- structure XML
- mappers
- règles de conversion
- normalisation des entités

### `MODE_DEBUG.md`
À consulter si présent, pour investiguer un échec de test, un écart de golden, ou une régression difficile.
Utilisation pertinente quand la demande concerne :
- diagnostic de bug
- comparaison de sorties
- stratégie de reproduction

---

## Règles de réponse attendues

- Répondre de façon ciblée.
- Proposer le minimum utile.
- Ne pas reformuler tout le projet si la demande porte sur un point local.
- Si une correction touche une zone sensible, le dire explicitement.
- Si plusieurs approches existent, privilégier la plus simple compatible avec les contraintes du projet.

---

## Raccourci mental

Quand la demande arrive :
- règle stable → `CLAUDE.md`
- tâche en cours → `TODO.md`
- dette / point ouvert → `BACKLOG.md`
- parsing PDF / tableaux → `MODE_PARSING.md`
- mapping XML → `MODE_MAPPING.md`
- debug / régression → `MODE_DEBUG.md`
