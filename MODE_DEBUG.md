# MODE_DEBUG — diagnostics, régressions et validation

## Objectif
Servir de mode de travail pour les échecs de test, les écarts de golden et les bugs difficiles à reproduire.

## Source de vérité
- les tests golden définissent le comportement attendu
- les fixtures de `tests/` ne doivent pas être modifiées sans validation explicite
- une divergence, même cosmétique, est une régression tant qu’elle n’a pas été bénie

## Workflow de base
1. reproduire le problème
2. générer une sortie temporaire
3. comparer à la référence
4. isoler l’écart
5. corriger localement
6. relancer les tests

## Commande centrale
```bash
uv run tests/test_runner.py
```

## Ce qu’il faut regarder en priorité
- différence XML caractère par caractère
- champs mécaniques manquants ou mal capturés
- texte absorbé par le mauvais bloc
- balises XSD invalides
- sortie Obsidian dégradée par une transformation XSLT

## Signaux d’alerte
- `*` résiduels dans le XML
- informations coupées après un changement de page
- valeurs de type ou de déclencheur mal reconnues
- perte de paragraphes ou de sous-blocs
- corrections trop larges qui cassent d’autres sorties

## Règle de conduite
- si un test échoue, s’arrêter
- ne pas bricoler une “réparation” globale avant d’avoir compris l’écart
- ne pas régénérer un golden sans validation explicite
- documenter les corrections ponctuelles dans le code avec un commentaire clair

## Cas typiques utiles
- corriger une regex trop large
- retracer une erreur de parsing sur un sort précis
- vérifier qu’un batch entier passe encore après un changement local
- comprendre pourquoi une description ou une table a disparu

## Sortie attendue
- diagnostic court
- cause probable
- correction minimale
- validation par les tests
