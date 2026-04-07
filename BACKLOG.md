# BACKLOG — dette technique et points ouverts

## Problèmes connus

### Parsing PDF
- texte après le bloc SCSEEC parfois mal délimité
- tableaux de traits ou tableaux décoratifs à filtrer
- cas limites sur les retours à la page

### XML / XSD
- `battleFormType` à modéliser
- gestion propre de `d'` / `de` dans les types de dégâts
- sorts à actions variables à représenter plus proprement
- ajout éventuel de `<source_id>` sur toutes les entités

### Obsidian / XSLT
- amélioration de la mise en forme des descriptions
- compatibilité XSLT 1.0 vs Saxon à vérifier plus tard

## Questions ouvertes
- fichiers monstres individuels vs agrégés
- meilleur format pour les données de formes de combat
- stratégie cross-livres à long terme

## À ne pas traiter sans décision explicite
- refactor global des mappers
- changement du schéma XML pivot
- réécriture du pipeline complet