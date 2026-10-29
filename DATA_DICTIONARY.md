# Dictionnaire des données (V2.0.0)

## data/raw/&lt;source&gt;/ — fichiers originaux et extractions littérales

- `MANIFEST.json` : par fichier, `url`, `date_collecte`, `http`, `content_type`, `octets`, `sha256`, `note`, `versionne` (faux = fichier conservé dans `_telechargements/`, non versionné pour raison de licence ou de taille ; récupérable par `tools/collect.py`, vérifiable par son empreinte).
- `*_extraction.csv` : valeurs **telles que publiées** (chaînes recopiées, sans conversion), nom de l'entité tel qu'écrit par la source, origine (page, figure, feuille).
  - Fraser `efw2025_extraction.csv` : `edition, nom_source, iso_source, annee, summary, rang, area1..area5, rang1..rang5, origine`.
  - Heritage `ief2026_extraction.csv` : `edition, nom_source, rang_mondial, rang_regional, score, variation, <12 composantes>, origine` ; « N/A » conservé tel quel.
  - V-Dem `vdem_v16_extraction.csv` : `edition, country_name, country_text_id, country_id, year, v2x_libdem, v2x_libdem_codelow, v2x_libdem_codehigh, v2x_libdem_sd, v2x_polyarchy, v2x_liberal` (CC BY-SA 4.0).
  - Freedom House `fiw2026_extraction.csv`, `fiw2013_2024_extraction.csv` : `edition, nom_source, type_source (pays/territoire), annee (année mesurée), total, pr, cl, statut, url_fiche, origine`.
  - `contexte/` : réponses brutes de l'API Banque mondiale (`wb_*.json`) et fichiers SDMX de l'OCDE.

## data/reference/

- `pays.csv` : `iso3` (identifiant stable ; `X-…` pour territoires sans code ISO), `iso2`, `nom_fr`, `nom_en`, `region` (région Banque mondiale ; pour un territoire, celle de l'État de rattachement), `groupe_revenu`, `type` (pays/territoire), `statut_politique`, `origine_referentiel`.
- `correspondances.csv` : `source, edition, nom_source, code_source, iso3, methode (code_identique | nom_identique | manuel), note`.

## data/processed/

- `observations.csv` — une ligne par (entité, source, édition, indicateur, année) :
  `iso3, source, edition, indicateur, libelle, role (principal | composante | incertitude), annee_reference, periode_debut, periode_fin, valeur_officielle (chaîne publiée), echelle_min, echelle_max, valeur_0_100, transformation, nom_dans_source, rang_officiel, statut_validation (extrait_verifie | hors_echelle_officielle), note, url_source, date_publication, date_collecte, sha256_source`.
  Indicateurs principaux : `efw_summary`, `ief_overall`, `v2x_libdem`, `fiw_total`. Une absence est une ligne absente (jamais 0).
- `contexte.csv` : `iso3, indicateur, libelle, unite, annee, valeur, source, url, fichier, date_collecte, date_revision, transformation, limites`.
- `anomalies.csv` : `niveau, code (HORS_ECHELLE, NON_CLASSE_HERITAGE, EDITION_NON_IMPORTEE…), iso3, source, detail`.
- `coordonnees.json` (déterministe) : `version_methodologie`, `configuration_officielle`, `scenario_officiel`, seuils, `empreinte_jeu_de_donnees` (SHA-256 des données traitées, du référentiel et de la configuration), `scenarios` (clé `sourceX|sourceY|mode` → `x`, `y`, `mode`, `officiel`, `comptes`, `points` : par entité `x`/`y` = {`v` 0-100, `off` valeur officielle, `ed`, `an`, `deb`, `fin`, `hors`} ou null, `ecart` en années, `statut` complet | x_seulement | y_seulement | aucune), `divergences`.

## data/contestations/contestations.csv

`date, iso3, source, indicateur, motif, reference, auteur, statut` — contestations documentées ; sans effet sur les données.

## docs/

`validation.json` (résultats test par test de la dernière validation), `comparaison_v1_v2.json` (comparaison descriptive avec l'ancienne grille).
