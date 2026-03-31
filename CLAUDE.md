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
pdf_sources/          → PDFs originaux (source of truth physique)
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
output/               → Fichiers intermédiaires de travail (temporaires)
obsidian_vault/       → Notes Obsidian générées (sortie finale actuelle)
tests/
  fixtures/           → XMLs de test/référence
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

## Points de vigilance

- **`xslt/` contient les XSD** : mélange de rôles (transformation + schéma). À factoriser en `schema/` si la complexité augmente.
- **`spell_to_obsidian.xsl` est en XSLT 1.0** alors que le README annonce Saxon (XSLT 3.0). Fonctionne en dégradé, mais ne profite pas des fonctionnalités 3.0.
- **`scripts/old/`** : à archiver ou supprimer quand les mappers courants sont stabilisés.
- Les **IDs XML sont des `xs:ID`** : unicité garantie par le XSD, mais le slug doit être stable entre les runs (actuellement basé sur le nom, pas sur un identifiant canonique PF2e).

---

## Objectif site web (horizon Phase 3+)

Le site cible est fonctionnellement équivalent à [Archives of Nethys](https://2e.aonprd.com/) mais en français :
- Navigation croisée : trait → définition + tous les éléments portant ce trait
- Source → liste de tous les éléments de ce livre/page
- Recherche full-text sur les descriptions
- Le XML structuré est conçu dès maintenant pour supporter ces liens (IDs stables, `<spellRef>`, `<source_id>` à venir)
- Technologie frontend à choisir au moment de la Phase 3 (le XML pivot permettra de générer JSON/HTML/autre sans retoucher les données)
