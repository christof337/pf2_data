# MODE_PARSING — extraction PDF, tableaux et heuristiques

## Objectif
Extraire proprement les tableaux et les blocs structurés depuis les PDFs Pathfinder 2e VF.

## Entrée
- PDF source
- éventuellement une plage de pages avec `--pages X-Y`

## Chaîne actuelle
- `pdfplumber` pour la détection géométrique
- `extract_pdf.py` injecte des marqueurs `[[TABLE_*]]`
- `parse_table_markers()` dans `utils.py` consomme ces marqueurs
- le mapper transforme ensuite les tables en XML

## Règles de traitement
- n'extraire que les pages nécessaires via extract_pdf.py, pour limiter au maximum la taille des .md générés (prendre une page avant une page après)
- exclure les tableaux décoratifs
- exclure les tableaux de traits
- exclure les tableaux trop courts
- exclure les blocs en all caps s’ils ne sont pas de vrais tableaux
- garder les tableaux utiles au traitement XML
- préserver les informations mécaniques, pas la seule apparence visuelle

## Cas sensibles
- tableaux coupés par changement de page
- faux positifs sur encadrés
- confusion entre contenu narratif et tableau
- lignes mécaniques comme `Déclencheur`, `Conditions`, `Coût`, `Conditions`
- entrées intensifiées ou blocs SCSEEC qui ne doivent pas être absorbés à tort

## Sortie attendue
- structure exploitable par le mapper
- aucune perte des tableaux utiles
- pas de pollution du texte narratif
- marqueurs bien résolus avant le mapping XML

## Commandes utiles
- extraction ciblée :
  `uv run scripts/extract_pdf.py --pages X-Y ...`
- validation :
  `uv run tests/test_runner.py`

## Règle de travail
- ne travailler que sur le sous-ensemble nécessaire
- éviter toute exploration hors du domaine tables/parsing
- si un tableau est douteux, le traiter explicitement plutôt que le laisser passer par accident
