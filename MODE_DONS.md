# MODE_DONS — parsing des dons (feats) Pathfinder 2e VF

## Plages de pages (Livre des Joueurs)

| Type                        | Pages    |
|-----------------------------|----------|
| Dons d'ascendance           | 40–83    |
| Dons de classe              | 90–205   |
| Dons d'archétype (multiclasse) | 215–223 |
| Dons généraux + compétences | 248–265  |

---

## Catégorisation des dons par trait

### 1. Dons d'ascendance
**Signal** : présence d'un trait d'ascendance dans le bloc de traits.

Traits d'ascendance reconnus (mettre en dur dans le mapper) :

```python
ANCESTRY_TRAITS = {
    # Ascendances de base
    "ELFE", "GNOME", "GOBELIN", "HALFELIN", "HUMAIN", "LÉCHI", "NAIN", "ORC",
    # Héritages polyvalents
    "CHANGELIN", "NÉPHILIM",
    # Héritages mixtes
    "AIUVARIN", "DROMAAR",
}
```

> Si un don présente UN de ces traits → `category="ancestry"`.

#### Cas particuliers d'ascendance
- **Héritages polyvalents** (changelin, néphilim) : héritages accessibles à toute ascendance.
  Leurs dons portent le trait "CHANGELIN" ou "NÉPHILIM", pas un trait d'ascendance classique.
- **Héritages mixtes** (aiuvarin = demi-elfe, dromaar = demi-orc) : héritages qui combinent
  deux ascendances et possèdent leurs propres dons avec les traits "AIUVARIN" / "DROMAAR".

---

### 2. Dons de classe
**Signal** : présence d'un trait de classe dans le bloc de traits.

```python
CLASS_TRAITS = {
    "BARDE", "DRUIDE", "GUERRIER", "MAGICIEN",
    "PRÊTRE", "RÔDEUR", "ROUBLARD", "SORCIER",
}
```

> Si un don présente UN de ces traits → `category="class"` + `class_trait` = le trait de classe.

---

### 3. Dons d'archétype (multiclasse)
**Pages** : 215–223. Un seul archétype par page.

**Signal de contexte** : titre de page "Archétype de {Classe}" (en-tête de page).

**Structure** :
- Le premier don de chaque archétype est le **don de dévouement** (ex. "Dévouement du Magicien").
- Les dons suivants ont en prérequis : `"Dévouement du {Classe}"`.

**Attribution** : relier chaque don à son archétype via l'en-tête de page, pas via les traits.

> `category="archetype"` + `archetype="magicien"` (slug de la classe).

---

### 4. Dons généraux
**Signal** : trait "GÉNÉRAL" présent dans le bloc de traits.

> `category="general"`.

---

### 5. Dons de compétence
**Signal** : traits "GÉNÉRAL" **et** "COMPÉTENCE" tous les deux présents.

**Compétence associée** : lire dans les **prérequis** (ex. "Athlétisme non qualifié").

> `category="skill"` + `skill` extrait des prérequis.

---

## Détection des catégories

Les quatre catégories principales (`ancestry`, `class`, `archetype`, `general`) sont **mutuellement exclusives**.

- trait dans `ANCESTRY_TRAITS` → `ancestry`
- trait dans `CLASS_TRAITS` → `class`
- en-tête de page "Archétype de {Classe}" → `archetype`
- trait "GÉNÉRAL" → `general`

**`skill` est une sous-catégorie de `general`** (et potentiellement d'`archetype`) :
- trait "GÉNÉRAL" **et** "COMPÉTENCE" → `general` + `is_skill=true`
- un don d'archétype peut également avoir le trait "COMPÉTENCE" → `archetype` + `is_skill=true`
- la compétence associée se lit dans les **prérequis** du don

---

## Structure d'un bloc don dans le PDF

Format typique en Markdown extrait :

```
**NOM DU DON** [N] DON M
TRAIT1 TRAIT2 TRAIT3
**Prérequis** texte libre
**Fréquence** texte libre
**Déclencheur** texte libre
**Conditions** texte libre
Texte de description.
**Spécial** texte libre
```

- `[N]` = nombre d'actions : `0` (libre), `1`, `2`, `3`, `9` (réaction). Absent = don passif.
- `M` = niveau du don (entier après le mot "DON").
- L'ordre des champs peut varier ; tous sont optionnels sauf nom et niveau.

---

## Mapping vers feat.xsd

| Champ PDF           | Élément XML       | Attribut XML      |
|---------------------|-------------------|-------------------|
| nom                 | `<name>`          | —                 |
| niveau              | `<level>`         | —                 |
| symbole d'action    | `<actions>`       | —                 |
| traits              | `<traits>`        | —                 |
| Prérequis           | `<prerequisites>` | —                 |
| Fréquence           | `<frequency>`     | —                 |
| Déclencheur         | `<trigger>`       | —                 |
| Conditions          | `<requirement>`   | —                 |
| description         | `<description>`   | —                 |
| Spécial             | `<special>`       | —                 |
| type (don/action)   | —                 | `type="don"`      |
| catégorie           | —                 | `category=` (à valider dans le schéma) |

> **Note schéma** : `feat.xsd` ne contient pas encore d'attribut `category` ni `archetype`.
> À ajouter avant le mapping si on veut les encoder dans le XML.

---

## Script cible
`scripts/feats_mapper.py` — à créer sur le modèle de `spells_mapper.py`.

Réutiliser depuis `utils.py` :
- `strip_metadata()`
- `split_bullet_list()`

Réutiliser depuis `slug_generator.py` :
- `generate_slug()` → ID au format `feat-{slug}`
