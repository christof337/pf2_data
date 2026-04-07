# MODE_PARSING — PDF, tableaux, et extraction

## Objectif
Extraire proprement les tableaux et les blocs structurés depuis les PDFs.

## Entrée
- PDF source
- éventuellement une plage de pages avec `--pages X-Y`

## Heuristiques actuelles
- pdfplumber pour la détection géométrique
- marqueurs `[[TABLE_*]]` injectés par l’extracteur
- `parse_table_markers()` consomme ces marqueurs

## Règles de traitement
- exclure les tableaux décoratifs
- exclure les tableaux de traits
- exclure les tableaux trop courts
- exclure les blocs en all caps s’ils ne sont pas de vrais tableaux
- garder les tableaux utiles au traitement XML

## Sortie attendue
- structure exploitable par le mapper
- aucune perte des tableaux utiles
- pas de pollution du texte narratif

## Commandes utiles
- extraction ciblée :
  `uv run scripts/extract_pdf.py --pages X-Y ...`
- validation :
  `uv run tests/test_runner.py`

## Pièges connus
- tableaux coupés par changement de page
- faux positifs sur encadrés
- confusion entre contenu narratif et tableau

## Règle de travail
- ne travailler que sur le sous-ensemble nécessaire
- éviter toute exploration hors du domaine tables/parsing