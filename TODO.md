# TODO — tâches en cours

## État actuel (2026-04-09)
- Batches 01 et 02 validés et bénis ; batch 03 en preview, en attente de validation
- Batch 04 en preview (régénéré) — pas encore de golden
- Les batches 05–10 ont des fixtures à jour mais pas encore de golden ni de preview
- `<cost>` et `<condition>` implémentés dans le schéma, le mapper et le XSL

→ Voir `CHANGELOG.md` pour l’historique complet des jalons.

## Priorité haute
- [ ] valider le preview batch 03 et bénir `tests/fixtures/test_sorts_03_ok.xml`
- [ ] continuer batches 04–10 progressivement (preview → validation → golden)

## Priorité moyenne
- [ ] reprendre le traitement par lot du Bestiaire complet
- [ ] traiter les autres familles de données : équipement, dons, dangers
- [ ] le trait émotion est trié alphabétiquement en dernier par erreur dans le xsl (discours captivant par exemple, dans sorts_batch_03.md dans preview). il devrait être avant manipulation
- [ ] les traditions et les traits des frappes doivent aussi être triés par ordre alphabétique dans le xsl
