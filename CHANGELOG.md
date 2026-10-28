# Journal des modifications

## Audit du 2026-10-28 (méthodologie 1.1 inchangée : aucun score officiel modifié)
- Audit complet : `AUDIT_REPORT.md`. Implémentation exacte (recalcul indépendant, 0 écart) ; 0 erreur factuelle ; 319 anomalies sur 160 entités, dues à des règles méthodologiques (couverture, proxys faibles, double comptage, asymétrie de couverture).
- Corrections de code (sans effet sur le score officiel) : moteur JS de l'explorateur aligné sur Python (une dimension de poids nul était comptée dans le minimum de dimensions ; arrondi des rangs 10⁻⁶ → 10⁻⁹) ; recalcul complet depuis les valeurs brutes dans le navigateur ; texte de méthodologie périmé (B1) ; test T08 sans critère (toujours « RÉUSSI ») ; code mort dans la fiabilité.
- Moteur paramétrable : règles de couverture (`config/dimensions.json` → défauts = V1.1), inclusion et poids internes par indicateur, contributions de chaque indicateur au score global.
- Registre de 12 décisions arbitrables (`config/decisions.json`, `DECISION_REGISTER.csv`), toutes au statut « proposée » ; approbation par `tools/approve.py` (crée la version 1.2). Scénario recommandé simulé dans `data/audit/`.
- Candidats collectés (hors score officiel) : B5n = B5 − B6 (OCDE) ; C4 propriété publique de l'économie (V-Dem v2clstown, vdemdata 16.0, `tools/collect_vdem.py`).
- Nouveaux livrables : `INDICATOR_DICTIONARY.csv` (niveaux de preuve 1-3), `DATA_QUALITY_REPORT.csv`, `ANOMALIES.csv`, `THEORETICAL_REFERENCES.md`.
- Tests : `tests/test_audit.py` (23 tests de cohérence, §24 du brief) ; `tests/test_html.py` étendu (parité JS/Python sur la méthode officielle et les 27 options, arbitrage, export/import) ; robustesse T13 (scénario recommandé) et T14 (comparaison de périodes 2020/2023). 51/51 tests réussis ; 0 échec critique.
- Empreinte du jeu de données : `1412b37d…` (le registre et les candidats en font partie) ; scores et rangs identiques à V1.1.

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
