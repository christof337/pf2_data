# BACKLOG — dette technique, bugs connus et décisions ouvertes

## Problèmes connus / différés

### Parsing PDF
- texte après le bloc SCSEEC parfois mal délimité
- sauts de ligne parfois aplatis dans les descriptions
- tableaux décoratifs ou faux tableaux à filtrer
- tableaux de traits à exclure
- cas limites sur les retours à la page
- certaines descriptions sont encore sensibles aux blocs coupés par changement de page

### XML / XSD
- `battleFormType` à modéliser pour les sorts de forme
- gestion propre de `d'` / `de` dans les types de dégâts
- sorts à actions variables à représenter plus proprement
- ajout éventuel de `<source_id>` sur toutes les entités
- trait de rareté à faire apparaître avant le reste, puis ordre alphabétique
- stratégie propre pour représenter certaines erreurs PDF sans casser la logique générale

### Obsidian / XSLT
- amélioration de la mise en forme des descriptions
- compatibilité XSLT 1.0 vs Saxon à vérifier plus tard
- rendu des entrées intensifiées à affiner si besoin
- rendu des blocs de stat spécifiques à certains sorts à formaliser

## Questions ouvertes
- fichiers monstres individuels vs agrégation dans un XML unique
- meilleure stratégie pour les données de formes de combat
- meilleure manière de représenter les corrections spécifiques à un seul sort
- stratégie cross-livres à long terme

## À ne pas traiter sans décision explicite
- refactor global des mappers
- changement du schéma XML pivot
- réécriture du pipeline complet
- suppression ou fusion massive des formats de sortie existants
