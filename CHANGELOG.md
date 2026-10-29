# Journal des modifications

## V2.0.1 — 2026-10-29 (interface seulement ; méthodologie 2.0.0 et données inchangées)
- Graphique : noms des pays du G20 affichés par défaut, placés sans chevauchement (trait de rappel si nécessaire) ; réglage « Seulement les pays cliqués » ou « Tous ».
- Clic ou toucher sur un point (point le plus proche, tolérance 18 px) : encadré avec le nom et les valeurs, nom conservé sur le graphique ; la fiche s'ouvre depuis l'encadré.
- Test d'interface ajouté (test_12) : 38 tests.

## V2.0.0 — 2026-10-29 (méthodologie 2.0.0) — rupture de méthode
- Demande du porteur du projet : remplacer l'indice composite par un repère à deux axes fondé exclusivement sur des indices internationaux publiés ; aucune notation propre au projet.
- Coordonnées officielles : X = Fraser EFW (édition 2025, données 2023, × 10) ; Y = V-Dem LDI (v16, données 2025, × 100). Comparaisons séparées : Heritage IEF 2026 (X) et Freedom House FIW 2026 + historique 2012-2023 (Y). Aucune moyenne entre sources.
- Nouvelle architecture : `config/`, `data/raw/<source>/` (manifestes SHA-256, extractions littérales), `data/reference/` (référentiel de 239 entités, correspondances explicites), `src/` (importeurs, transformation unique, sélection unique), `tools/`, `tests/`, `index.html`.
- Données contextuelles (Banque mondiale, OCDE) conservées hors des coordonnées.
- Interface refondue : nuage de points (zoom, déplacement), mode comparaison signalé, période « plus récente » ou « année commune », fiches pays, données incomplètes, correspondances, contestations sans effet sur les données.
- 37 tests automatisés (26 pipeline, 11 interface) ; validation bloquante en cas d'échec critique.
- Ancienne méthode retirée de l'interface et archivée intégralement dans `archive/v1/` (reproductible en place) ; éditions V1.0 et V1.1 conservées dans `editions/`. Les scores V1 et les coordonnées V2 ne sont pas comparables (`docs/AUDIT_ANCIENNE_GRILLE.md`).
- Limite connue : EFW 2026 (données 2024) publiée mais non importée (fichiers inaccessibles depuis l'environnement de travail).

## V1.1 — 2026-10-28 (méthodologie 1.1) — changement méthodologique
- Demande du porteur du projet : cotisations, impôts et taxes sont tous des « prélèvements », sans distinction ; le taux de taxation du travail est un indicateur important.
- Retrait de B1 (cotisations sociales en % des recettes). Ajout de B5 (prélèvements obligatoires totaux, % PIB), B6 (impôt sur le revenu + cotisations + taxes sur salaires, % PIB), B7 (coin fiscal sur le travail, OCDE Taxing Wages). Sources OCDE ajoutées à `data/raw` (`oecd_rev_global.csv`, `oecd_tw_comp.csv`).
- Nouveaux principes P18 (p. 35), P19 (p. 283 : la cotisation est « une taxe […] qui frappe les salaires »), P20 (p. 215) ; citations vérifiées 34/34.
- Dimension B : 6 indicateurs ; pondérations inchangées (45/20/20/15). Effet du changement : voir `docs/COMPARAISON_V1.0_V1.1.md` (Spearman 0,957 ; Danemark 2e → 14e).
- Test T03 corrigé : rapprochement Freedom House par nom exact seulement ; les observations non rapprochables sont comptées et signalées au lieu d'être tolérées.

## V1.0 — 2026-10-28 (méthodologie 1.0, données 2023)
- Première édition : 237 entités, 17 indicateurs (A:6, B:4, C:3, D:4), pondérations 45/20/20/15.
- Corpus : *Capitalisme et liberté* (Leduc.s 2010) ; 17 principes, 30 citations vérifiées littéralement page par page.
- Règle propre à la V1 : score global exigeant la dimension A et au moins 2 dimensions (voir `config/dimensions.json`).
- Explorateur HTML autonome, 12 tests de robustesse, 18 tests unitaires du moteur, 7 tests de l'interface.
- Toute modification d'indicateur, de pondération ou de normalisation créera une nouvelle version (V1.1, V2.0…) avec comparaison à méthodologie constante / changée.
