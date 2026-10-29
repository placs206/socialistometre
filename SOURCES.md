# Sources, éditions, licences (V2.0.0)

Définitions complètes et machine-lisibles : `config/sources.json`. Empreintes et dates de collecte : `data/raw/<source>/MANIFEST.json`.

## Fraser Institute — Economic Freedom of the World (axe X, principal)

- **Importée : EFW 2025 Annual Report** (Gwartney, Lawson, Murphy et al., septembre 2025), données **2023**, 165 pays et territoires, échelle 0-10. Composantes : 1 Taille de l'État, 2 Système juridique et droits de propriété, 3 Monnaie saine, 4 Liberté d'échanger internationalement, 5 Réglementation.
- Fichier : rapport PDF officiel complet, copie hébergée par le Liberales Institut (membre de l'Economic Freedom Network) — https://www.libinst.ch/wp-content/uploads/2025/09/EFOTW-2025.pdf (SHA-256 au manifeste). Extraction : figures 1.1a-b (indice et rang, p. 15-16) et tableau 1.2 (domaines et rangs, p. 17-21), par coordonnées des mots ; contrôles : indice = moyenne des 5 domaines à 0,01 près (méthode officielle, 165/165), rangs cohérents (165/165).
- **Non importée : EFW 2026 Annual Report** (octobre 2026, données 2024). fraserinstitute.org et cato.org renvoient une page anti-robots (Cloudflare 403, Incapsula) ; l'API du site efotw.org n'a pas été appelée faute d'autorisation. Procédure d'import dans le README.
- Méthodologie : https://www.fraserinstitute.org/economic-freedom/approach. Attribution requise. Le PDF n'est pas redistribué.

## V-Dem Institute — Liberal Democracy Index (axe Y, principal)

- **Importée : V-Dem Dataset v16** (mars 2026), country-year, `v2x_libdem` (0-1) avec intervalle HPD à 68 % (`_codelow`, `_codehigh`), composantes `v2x_polyarchy` et `v2x_liberal` ; années 2000-2025 conservées, 179 entités en 2025.
- Fichier : paquet R officiel `vdemdata` 16.0 (V-Dem Institute) — https://github.com/vdeminstitute/vdemdata, commit f4dd269 « v16 release » (17 mars 2026), `data/vdem.RData`. Le téléchargement sur v-dem.net passe par un formulaire nominatif (courriel) qui n'a pas été rempli au nom de l'utilisateur. Échelle vérifiée dans le codebook v16 (§ 2.1.2) : https://v-dem.net/documents/70/codebook_v16.pdf.
- Licence : **CC BY-SA 4.0**. L'extrait `data/raw/vdem/vdem_v16_extraction.csv` est redistribué sous la même licence. Citation : Coppedge, M., et al. 2026. « V-Dem Country-Year Dataset v16 ». Varieties of Democracy (V-Dem) Project.

## Heritage Foundation — Index of Economic Freedom (axe X, comparaison)

- **Importée : 2026 Index of Economic Freedom** (février 2026), période 2e semestre 2024 – 1er semestre 2025 (données arrêtées au 30 juin 2025), 184 économies dont 176 classées et 8 « N/A » (Afghanistan, Irak, Libye, Liechtenstein, Somalie, Syrie, Ukraine, Yémen ; composantes publiées conservées). 12 composantes 0-100, pondérées également.
- Fichier : https://static.heritage.org/index/pdf/2026/2026_indexofeconomicfreedom.pdf (tableau « World Rankings », p. 19-23). Ordre des colonnes vérifié par les coordonnées des en-têtes pivotés. Les pages HTML de heritage.org sont inaccessibles depuis l'environnement (Cloudflare).
- © The Heritage Foundation ; PDF non redistribué, valeurs extraites avec attribution.

## Freedom House — Freedom in the World (axe Y, comparaison)

- **Importée : FIW 2026** (année 2025), 208 pays et territoires : score total /100, droits politiques (0-40), libertés civiles (0-60), statut. Source : tableau officiel https://freedomhouse.org/countries/freedom-world/scores (liens d'édition « /freedom-world/2026 » vérifiés pour chaque ligne). Aucun tableur FIW 2026 téléchargeable trouvé.
- **Importée (historique) : All_data_FIW_2013-2024.xlsx** (éditions 2013-2024 = années 2012-2023), fichier déjà collecté pour la V1 (SHA-256 identique).
- **Non importée : FIW 2025** (année 2024) — aucun fichier trouvé ; l'année 2024 est absente, sans interpolation.
- Licence : usage personnel, académique et non lucratif gratuit avec attribution ; usage commercial sur demande (https://freedomhouse.org/data-request).

## Données contextuelles (hors coordonnées)

Banque mondiale WDI (API, révision 2026-10-08) : GC.XPN.TOTL.GD.ZS, GC.TAX.TOTL.GD.ZS, NE.CON.GOVT.ZS, GC.REV.SOCL.ZS, NY.GDP.PCAP.PP.KD (licence CC BY 4.0). OCDE : Global Revenue Statistics, Taxing Wages, Tax Database (fichiers collectés le 2026-10-28 pour la V1, réutilisés).
