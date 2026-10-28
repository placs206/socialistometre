#!/usr/bin/env python3
"""Construit les jeux de données traités du Socialistomètre à partir de data/raw/.

Sorties (data/processed/) :
  pays.csv            – référentiel des pays et territoires (identifiant stable, statut, région…)
  observations.csv    – une ligne par (pays, indicateur) avec valeur brute, année, source, URL, etc.
  anomalies.csv       – journal des anomalies détectées (codes non appariés, valeurs rejetées/extrêmes…)
  indicateurs_alt.csv – observations des variantes de sensibilité (A1alt, C2alt)

Aucune valeur n'est inventée ni substituée : une observation absente reste absente.
Usage : python3 tools/build_dataset.py
"""
import csv, json, os, re, statistics, unicodedata
import openpyxl
from babel import Locale

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.environ.get("SOCIO_OUT") or os.path.join(ROOT, "data", "processed")   # SOCIO_OUT : test de période (T14) uniquement
CFG = os.path.join(ROOT, "config")

MANIFEST = json.load(open(os.path.join(RAW, "MANIFEST.json"), encoding="utf-8"))
COLLECT_DATE = MANIFEST["genere_le"]
DIM = json.load(open(os.path.join(CFG, "dimensions.json"), encoding="utf-8"))
Y_MIN, Y_MAX = DIM["fenetre_annees"]
# Variables d'environnement réservées au test de période (tools/run_robustness.py, T14) ; sans elles : édition officielle.
if os.environ.get("SOCIO_FENETRE"):
    Y_MIN, Y_MAX = (int(x) for x in os.environ["SOCIO_FENETRE"].split(","))
FH_EDITION = int(os.environ.get("SOCIO_FH_EDITION", "2024"))
PMR_ANNEE = os.environ.get("SOCIO_PMR_ANNEE", "2023")
IND = json.load(open(os.path.join(CFG, "indicateurs.json"), encoding="utf-8"))

anomalies = []


def anomalie(niveau, code, detail, iso3="", indicateur=""):
    anomalies.append({"niveau": niveau, "code": code, "iso3": iso3, "indicateur": indicateur, "detail": detail})


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ------------------------------------------------------------------ référentiel pays
REGIONS_FR = {"East Asia & Pacific": "Asie de l'Est et Pacifique", "Europe & Central Asia": "Europe et Asie centrale",
              "Latin America & Caribbean": "Amérique latine et Caraïbes", "Middle East & North Africa": "Moyen-Orient et Afrique du Nord",
              "North America": "Amérique du Nord", "South Asia": "Asie du Sud", "Sub-Saharan Africa": "Afrique subsaharienne",
              "Middle East, North Africa, Afghanistan & Pakistan": "Moyen-Orient, Afrique du Nord, Afghanistan et Pakistan"}
REGION_FH_FR = {"Africa": "Afrique", "Americas": "Amériques", "Asia": "Asie", "Eurasia": "Eurasie", "Europe": "Europe", "Middle East": "Moyen-Orient"}
INCOME_FR = {"High income": "Revenu élevé", "Upper middle income": "Revenu intermédiaire supérieur",
             "Lower middle income": "Revenu intermédiaire inférieur", "Low income": "Revenu faible", "Not classified": "Non classé"}

# Territoires non souverains ou statut contesté (affiliation / statut documentés à la main)
STATUT = {
    "ABW": "Pays constitutif du Royaume des Pays-Bas", "ASM": "Territoire non incorporé des États-Unis",
    "BMU": "Territoire britannique d'outre-mer", "CHI": "Dépendances de la Couronne britannique (Jersey et Guernesey)",
    "CUW": "Pays constitutif du Royaume des Pays-Bas", "CYM": "Territoire britannique d'outre-mer",
    "FRO": "Territoire autonome du Royaume du Danemark", "GIB": "Territoire britannique d'outre-mer",
    "GRL": "Territoire autonome du Royaume du Danemark", "GUM": "Territoire non incorporé des États-Unis",
    "HKG": "Région administrative spéciale de la Chine", "IMN": "Dépendance de la Couronne britannique",
    "MAC": "Région administrative spéciale de la Chine", "MAF": "Collectivité d'outre-mer de la France",
    "MNP": "Commonwealth rattaché aux États-Unis", "NCL": "Collectivité sui generis de la France",
    "PRI": "Territoire non incorporé des États-Unis", "PYF": "Collectivité d'outre-mer de la France",
    "SXM": "Pays constitutif du Royaume des Pays-Bas", "TCA": "Territoire britannique d'outre-mer",
    "VGB": "Territoire britannique d'outre-mer", "VIR": "Territoire non incorporé des États-Unis",
    "PSE": "Territoire palestinien (statut contesté ; Cisjordanie et Gaza agrégées par la Banque mondiale)",
    "XKX": "Indépendance partiellement reconnue", "TWN": "Statut politique contesté ; statistiques distinctes (OCDE, Freedom House)",
}
FH_MAP = {  # noms Freedom House → ISO3 lorsque le nom diffère de celui de la Banque mondiale
    "Bahamas": "BHS", "Brunei": "BRN", "Congo (Brazzaville)": "COG", "Congo (Kinshasa)": "COD", "Czech Republic": "CZE",
    "Egypt": "EGY", "Hong Kong": "HKG", "Iran": "IRN", "Kyrgyzstan": "KGZ", "Laos": "LAO", "Micronesia": "FSM", "Nauru": "NRU",
    "North Korea": "PRK", "Russia": "RUS", "Slovakia": "SVK", "Somalia": "SOM", "South Korea": "KOR", "Syria": "SYR",
    "Taiwan": "TWN", "The Gambia": "GMB", "Turkey": "TUR", "Venezuela": "VEN", "Vietnam": "VNM", "Yemen": "YEM"}
FH_SYNTH = {  # territoires Freedom House sans code ISO3 : identifiant interne « X-… », nom français, statut
    "Abkhazia": ("X-ABK", "Abkhazie", "Territoire séparatiste de Géorgie, contrôlé de facto avec soutien russe"),
    "Crimea": ("X-CRM", "Crimée", "Territoire d'Ukraine annexé par la Russie en 2014 (annexion non reconnue internationalement)"),
    "Eastern Donbas": ("X-DON", "Donbass oriental", "Territoire d'Ukraine sous contrôle russe et séparatiste"),
    "Gaza Strip": ("X-GAZ", "Bande de Gaza", "Territoire palestinien (statut contesté)"),
    "Indian Kashmir": ("X-KAI", "Cachemire indien", "Territoire contesté entre l'Inde et le Pakistan, administré par l'Inde"),
    "Nagorno-Karabakh": ("X-NKR", "Haut-Karabagh", "Territoire contesté entre l'Azerbaïdjan et l'Arménie (édition FH 2024 : situation antérieure à fin 2023)"),
    "Northern Cyprus": ("X-NCY", "Chypre du Nord", "Entité séparatiste reconnue seulement par la Turquie"),
    "Pakistani Kashmir": ("X-KAP", "Cachemire pakistanais", "Territoire contesté entre l'Inde et le Pakistan, administré par le Pakistan"),
    "Somaliland": ("X-SML", "Somaliland", "État autoproclamé, non reconnu, séparé de la Somalie"),
    "South Ossetia": ("X-OSS", "Ossétie du Sud", "Territoire séparatiste de Géorgie, contrôlé de facto avec soutien russe"),
    "Tibet": ("X-TIB", "Tibet", "Région autonome de la Chine"),
    "Transnistria": ("X-TRN", "Transnistrie", "Territoire séparatiste de la Moldavie"),
    "West Bank": ("X-WBK", "Cisjordanie", "Territoire palestinien occupé (statut contesté)"),
    "Western Sahara": ("X-ESH", "Sahara occidental", "Territoire non autonome, statut contesté"),
}

fr = Locale("fr").territories
wb_raw = json.load(open(os.path.join(RAW, "wb_countries.json"), encoding="utf-8"))[1]
pays = {}
for c in wb_raw:
    if c["region"]["id"] == "NA" or c["region"]["value"].strip() == "Aggregates":
        continue
    iso3 = c["id"]
    nom_fr = "Îles Anglo-Normandes" if iso3 == "CHI" else fr.get(c["iso2Code"], c["name"])
    pays[iso3] = {"iso3": iso3, "iso2": c["iso2Code"], "nom_fr": nom_fr, "nom_en": c["name"],
                  "region": REGIONS_FR.get(c["region"]["value"].strip(), c["region"]["value"].strip()),
                  "groupe_revenu": INCOME_FR.get(c["incomeLevel"]["value"], c["incomeLevel"]["value"]),
                  "type": "territoire" if iso3 in STATUT and iso3 not in ("XKX",) else "pays",
                  "statut_politique": STATUT.get(iso3, "État souverain"), "origine_referentiel": "Banque mondiale"}

# Freedom House
wbk = openpyxl.load_workbook(os.path.join(RAW, "freedomhouse_fiw_2013-2024.xlsx"), read_only=True, data_only=True)
rows = list(wbk["FIW13-24"].iter_rows(values_only=True))
hdr = rows[1]
fh_rows = [dict(zip(hdr, r)) for r in rows[2:] if r[0] and r[3] == FH_EDITION]
wb_by_name = {norm(p["nom_en"]): k for k, p in pays.items()}
fh_by_iso = {}
for d in fh_rows:
    name = d["Country/Territory"]
    if name in FH_SYNTH:
        iso3, nom_fr, statut = FH_SYNTH[name]
        pays[iso3] = {"iso3": iso3, "iso2": "", "nom_fr": nom_fr, "nom_en": name, "region": REGION_FH_FR.get(d["Region"], d["Region"]),
                      "groupe_revenu": "Non classé", "type": "territoire", "statut_politique": statut, "origine_referentiel": "Freedom House"}
    elif name in FH_MAP:
        iso3 = FH_MAP[name]
        if iso3 not in pays:  # Taïwan : absent de la Banque mondiale
            pays[iso3] = {"iso3": iso3, "iso2": "TW", "nom_fr": fr.get("TW", name), "nom_en": "Taiwan", "region": "Asie de l'Est et Pacifique",
                          "groupe_revenu": "Non classé", "type": "territoire", "statut_politique": STATUT["TWN"],
                          "origine_referentiel": "Freedom House / OCDE"}
    elif norm(name) in wb_by_name:
        iso3 = wb_by_name[norm(name)]
    else:
        anomalie("erreur", "FH_NON_APPARIE", f"Entité Freedom House sans identifiant : {name}")
        continue
    fh_by_iso[iso3] = d

# Territoires présents dans les statistiques OCDE mais absents du référentiel Banque mondiale
EXTRA_OCDE = {
    "AIA": ("AI", "Anguilla", "Amérique latine et Caraïbes", "Territoire britannique d'outre-mer"),
    "MSR": ("MS", "Montserrat", "Amérique latine et Caraïbes", "Territoire britannique d'outre-mer"),
    "COK": ("CK", "Cook Islands", "Asie de l'Est et Pacifique", "État en libre association avec la Nouvelle-Zélande"),
    "GGY": ("GG", "Guernsey", "Europe et Asie centrale", "Dépendance de la Couronne britannique (bailliage de Guernesey)"),
    "JEY": ("JE", "Jersey", "Europe et Asie centrale", "Dépendance de la Couronne britannique (bailliage de Jersey)")}
for iso3, (iso2, en, reg, st) in EXTRA_OCDE.items():
    pays[iso3] = {"iso3": iso3, "iso2": iso2, "nom_fr": fr.get(iso2, en), "nom_en": en, "region": reg, "groupe_revenu": "Non classé",
                  "type": "territoire", "statut_politique": st, "origine_referentiel": "OCDE (hors référentiel Banque mondiale)"}
anomalie("info", "CHEVAUCHEMENT_TERRITOIRES", "La Banque mondiale agrège Jersey et Guernesey (CHI) ; l'OCDE les publie séparément (JEY, GGY). Aucune variable commune dans l'indice.", "CHI")

# ------------------------------------------------------------------ observations
obs, obs_alt = [], []


def clean_status(code, val, lo, hi, iso3):
    if val is None:
        return None
    if lo is not None and (val < lo or val > hi):
        anomalie("rejet", "HORS_PLAGE", f"valeur {val} hors plage [{lo}, {hi}] : rejetée", iso3, code)
        return None
    return val


IND_BY_ID = {i["id"]: i for i in IND["indicateurs"]}
for alt in IND["alternatives_sensibilite"]:
    IND_BY_ID[alt["id"]] = alt
RANGES = {"A1": (0, 100), "A1alt": (0, 100), "A2": (0, 6), "A3": (0, 6), "A4": (-2.6, 2.6), "A5": (-2.6, 2.6), "A6": (0, 4),
          "B5": (0, 100), "B5n": (0, 100), "B6": (0, 100), "B7": (0, 100), "B2": (0, 100), "B3": (0, 100), "B4": (0, 2), "C1": (0, 6), "C2": (0, 100), "C2alt": (0, 100),
          "C3": (0, 100), "C4": (0, 4), "D1": (-2.6, 2.6), "D2": (-4, 40), "D3": (0, 16), "D4": (0, 12)}
UNITE = {i["id"]: i["unite"] for i in IND["indicateurs"]}
UNITE["A1alt"] = "%"; UNITE["C2alt"] = "% des inscrits"; UNITE["B5n"] = "% du PIB"; UNITE["C4"] = "échelle 0-4"


def add(ind_id, iso3, val, year, source, url, fichier, transfo, revision="", limites="", alt=False):
    lo, hi = RANGES[ind_id]
    v = clean_status(ind_id, val, lo, hi, iso3)
    if v is None:
        return
    rec = {"iso3": iso3, "indicateur": ind_id, "valeur_brute": round(v, 6), "unite": UNITE[ind_id], "annee": year,
           "source": source, "url_source": url, "date_collecte": COLLECT_DATE, "date_revision": revision,
           "transformation": transfo, "statut_validation": "valide", "limites_comparabilite": limites, "fichier_brut": fichier}
    (obs_alt if alt else obs).append(rec)


def load_wb(code):
    pages = json.load(open(os.path.join(RAW, f"wb_{code}.json"), encoding="utf-8"))
    rev = pages[0][0].get("lastupdated", "")
    recs = {}
    for pg in pages:
        for r in pg[1] or []:
            iso3 = r.get("countryiso3code")
            if iso3 in pays and r["value"] is not None:
                y = int(r["date"])
                if Y_MIN <= y <= Y_MAX:
                    if iso3 not in recs or y > recs[iso3][0]:
                        recs[iso3] = (y, float(r["value"]))
    return recs, rev


WBMAP = {"A1": "TM.TAX.MRCH.SM.AR.ZS", "A1alt": "TM.TAX.MRCH.WM.AR.ZS", "C2": "SE.PRM.PRIV.ZS",
         "C2alt": "SE.SEC.PRIV.ZS", "C3": "NE.CON.GOVT.ZS", "A4": "GOV_WGI_RL.EST", "A5": "GOV_WGI_RQ.EST", "D1": "GOV_WGI_VA.EST"}
for ind_id, code in WBMAP.items():
    recs, rev = load_wb(code)
    src = IND_BY_ID[ind_id].get("source", "Banque mondiale (WDI)")
    url = IND_BY_ID[ind_id].get("url") or f"https://data.worldbank.org/indicator/{code}"
    if ind_id in ("A1alt", "C2alt"):
        src = "Banque mondiale (WDI)"; url = f"https://data.worldbank.org/indicator/{code}"
    for iso3, (y, v) in recs.items():
        add(ind_id, iso3, v, y, src, url, f"wb_{code}.json",
            f"dernière valeur disponible dans la fenêtre {Y_MIN}-{Y_MAX} ; aucune transformation de valeur", revision=rev,
            alt=ind_id.endswith("alt"))

# OCDE : PMR
def read_csv(name):
    return list(csv.DictReader(open(os.path.join(RAW, name), encoding="utf-8")))


def oecd_known(area, ind_id):
    if area in pays:
        return True
    anomalie("info", "CODE_OCDE_HORS_REFERENTIEL", f"Code OCDE {area} non rattaché à une entité du référentiel", area, ind_id)
    return False


pmr_main = read_csv("oecd_pmr.csv")
pmr_wbg = read_csv("oecd_pmr_wbg.csv")
pm = {}  # (area, measure) -> (valeur, source_fichier)
for fname, rows_ in (("oecd_pmr.csv", pmr_main), ("oecd_pmr_wbg.csv", pmr_wbg)):
    for r in rows_:
        if r["TIME_PERIOD"] == PMR_ANNEE and r["OBS_VALUE"] != "":
            k = (r["REF_AREA"], r["MEASURE"])
            v = float(r["OBS_VALUE"])
            if k in pm and abs(pm[k][0] - v) > 1e-6:
                anomalie("avertissement", "PMR_DOUBLON_DIVERGENT", f"{k} : {pm[k][0]} (OCDE) ≠ {v} (OCDE-BM)", k[0], "A2/A3/C1")
            pm.setdefault(k, (v, fname))
PMR_URL = "https://www.oecd.org/en/topics/product-market-regulation.html"
PROFS = ["LAWYERS", "ACCOUNTANTS", "ARCHITECTS", "ENGINEERS", "ESTATEAGENTS"]
areas = sorted({a for a, _ in pm})
for a in areas:
    if not oecd_known(a, "PMR"):
        continue
    lim = "Source OCDE-Banque mondiale pour les économies non membres : méthodologie PMR commune" if pm.get((a, "PMR"), (0, ""))[1] == "oecd_pmr_wbg.csv" else ""
    if all((a, m) in pm for m in PROFS):
        add("A2", a, sum(pm[(a, m)][0] for m in PROFS) / 5, int(PMR_ANNEE), IND_BY_ID["A2"]["source"], PMR_URL, "oecd_pmr.csv / oecd_pmr_wbg.csv",
            "moyenne arithmétique des 5 sous-indices professionnels (LAWYERS, ACCOUNTANTS, ARCHITECTS, ENGINEERS, ESTATEAGENTS)", limites=lim)
    elif any((a, m) in pm for m in PROFS):
        anomalie("avertissement", "A2_INCOMPLET", "sous-indices professionnels incomplets : A2 non calculé", a, "A2")
    for ind_id, meas in (("A3", "PRICE"), ("C1", "PUBLIC_OWNER")):
        if (a, meas) in pm:
            add(ind_id, a, pm[(a, meas)][0], int(PMR_ANNEE), IND_BY_ID[ind_id]["source"], PMR_URL, pm[(a, meas)][1], f"sous-indice PMR {meas} repris tel quel", limites=lim)

# OCDE : IS combiné
cit = {}
for r in read_csv("oecd_cit.csv"):
    if r["MEASURE"] == "CIT_C" and r["TARGETING"] == "ST" and r["SECTOR"] == "S13" and r["OBS_VALUE"] != "":
        y = int(r["TIME_PERIOD"])
        if Y_MIN <= y <= Y_MAX and (r["REF_AREA"] not in cit or y > cit[r["REF_AREA"]][0]):
            cit[r["REF_AREA"]] = (y, float(r["OBS_VALUE"]))
for a, (y, v) in cit.items():
    if oecd_known(a, "B3"):
        add("B3", a, v, y, IND_BY_ID["B3"]["source"], IND_BY_ID["B3"]["url"], "oecd_cit.csv", "taux statutaire combiné (CIT_C, secteur S13, ciblage ST) repris tel quel")

# OCDE : taux supérieur IR
pit = {}
for r in read_csv("oecd_pit_top.csv"):
    if r["MEASURE"] == "TS_PIT" and r["OBS_VALUE"] != "":
        y = int(r["TIME_PERIOD"])
        if Y_MIN <= y <= Y_MAX and (r["REF_AREA"] not in pit or y > pit[r["REF_AREA"]][0]):
            pit[r["REF_AREA"]] = (y, float(r["OBS_VALUE"]))
for a, (y, v) in pit.items():
    if oecd_known(a, "B2"):
        add("B2", a, v, y, IND_BY_ID["B2"]["source"], IND_BY_ID["B2"]["url"], "oecd_pit_top.csv", "taux supérieur statutaire (TS_PIT) repris tel quel")

# OCDE : salaire minimum relatif (médiane)
mw = {}
for r in read_csv("oecd_min2ave.csv"):
    if r["AGGREGATION_OPERATION"] == "MEDIAN" and r["OBS_VALUE"] != "":
        y = int(r["TIME_PERIOD"])
        if Y_MIN <= y <= Y_MAX and (r["REF_AREA"] not in mw or y > mw[r["REF_AREA"]][0]):
            mw[r["REF_AREA"]] = (y, float(r["OBS_VALUE"]))
mw_units = {r["UNIT_MEASURE"] for r in read_csv("oecd_min2ave.csv")}
for a, (y, v) in mw.items():
    if oecd_known(a, "B4"):
        vv = v / 100.0 if v > 2 else v  # l'unité source est un pourcentage du salaire (PT_WG_A_SAL_FT)
        add("B4", a, vv, y, IND_BY_ID["B4"]["source"], IND_BY_ID["B4"]["url"], "oecd_min2ave.csv",
            "valeur en % du salaire médian divisée par 100 (ratio)")

# OCDE (V1.1) : prélèvements obligatoires totaux et sur le travail (% PIB), dernière année de la fenêtre
rev = {}
for r in read_csv("oecd_rev_global.csv"):
    if r["OBS_VALUE"] != "" and r["SECTOR"] == "S13" and r["UNIT_MEASURE"] == "PT_B1GQ":
        y = int(r["TIME_PERIOD"])
        if Y_MIN <= y <= Y_MAX:
            rev.setdefault(r["REF_AREA"], {}).setdefault(r["STANDARD_REVENUE"], {})[y] = float(r["OBS_VALUE"])
REV_URL = IND_BY_ID["B5"]["url"]
for a, d in sorted(rev.items()):
    if a in ("A9", "SO", "F", "OECD_REP") or not oecd_known(a, "B5"):
        continue
    if "_T" in d:
        y = max(d["_T"]); add("B5", a, d["_T"][y], y, IND_BY_ID["B5"]["source"], REV_URL, "oecd_rev_global.csv", f"total des recettes (code _T), % du PIB, secteur S13 ; dernière année de la fenêtre {Y_MIN}-{Y_MAX} ; repris tel quel")
    comps = ("T_1100", "T_2000", "T_3000")
    if all(c in d for c in comps):
        ys = set.intersection(*[set(d[c]) for c in comps])
        if ys:
            y = max(ys); add("B6", a, sum(d[c][y] for c in comps), y, IND_BY_ID["B6"]["source"], REV_URL, "oecd_rev_global.csv", "somme des codes 1100 (impôt sur le revenu), 2000 (cotisations sociales), 3000 (taxes sur les salaires), % du PIB, même année")
            # Candidat d'audit (décision DEC-05) : prélèvements hors revenus des personnes et travail = total − (1100+2000+3000), même année
            if "_T" in d and y in d["_T"]:
                add("B5n", a, d["_T"][y] - sum(d[c][y] for c in comps), y, IND_BY_ID["B5"]["source"], REV_URL, "oecd_rev_global.csv",
                    "code _T moins (1100 + 2000 + 3000), % du PIB, même année que B6 ; supprime l'inclusion arithmétique de B6 dans B5", alt=True)
        else:
            anomalie("avertissement", "B6_ANNEES_DISJOINTES", "composantes publiées pour des années différentes : B6 non calculé", a, "B6")
    elif any(c in d for c in comps):
        anomalie("info", "B6_INCOMPLET", "composantes manquantes (" + ", ".join(c for c in comps if c not in d) + ") : B6 non calculé, aucune valeur supposée nulle", a, "B6")

# OCDE (V1.1) : coin fiscal moyen (célibataire sans enfant, 100 % du salaire moyen)
tw = {}
for r in read_csv("oecd_tw_comp.csv"):
    if (r["MEASURE"] == "AV_TW" and r["HOUSEHOLD_TYPE"] == "S_C0" and r["INCOME_PRINCIPAL"] == "AW100" and r["UNIT_MEASURE"] == "PT_COS_LB" and r["OBS_VALUE"] != ""):
        y = int(r["TIME_PERIOD"])
        if Y_MIN <= y <= Y_MAX and (r["REF_AREA"] not in tw or y > tw[r["REF_AREA"]][0]):
            tw[r["REF_AREA"]] = (y, float(r["OBS_VALUE"]))
for a, (y, v) in sorted(tw.items()):
    if a != "OECD_REP" and oecd_known(a, "B7"):
        add("B7", a, v, y, IND_BY_ID["B7"]["source"], IND_BY_ID["B7"]["url"], "oecd_tw_comp.csv", "coin fiscal moyen AV_TW (S_C0, AW100, % du coût du travail) repris tel quel")

# V-Dem (candidat d'audit C4, décision DEC-07) : propriété publique de l'économie, échelle d'origine 0-4 (v2clstown_osp)
VDEM_P = os.path.join(RAW, "vdem_extrait.csv")
if os.path.exists(VDEM_P):
    VDEM_SPECIAL = {"SML": "X-SML"}          # Somaliland
    VDEM_SKIP = {"PSE": "V-Dem « Palestine/West Bank » ≠ agrégat Banque mondiale « Cisjordanie et Gaza » (PSE) : non rapproché",
                 "PSG": "V-Dem « Palestine/Gaza » sans équivalent exact dans le référentiel : non rapproché",
                 "ZZB": "Zanzibar : sans équivalent dans le référentiel"}
    vd = {}
    for r in csv.DictReader(open(VDEM_P, encoding="utf-8")):
        if r["v2clstown_osp"] in ("", "NA"):
            continue
        y = int(float(r["year"]))
        if Y_MIN <= y <= Y_MAX:
            c = r["country_text_id"]
            if c in VDEM_SKIP:
                continue
            iso3 = VDEM_SPECIAL.get(c, c)
            if iso3 not in pays:
                anomalie("info", "VDEM_HORS_REFERENTIEL", f"Code V-Dem {c} ({r['country_name']}) non rattaché", c, "C4"); continue
            if iso3 not in vd or y > vd[iso3][0]:
                vd[iso3] = (y, float(r["v2clstown_osp"]))
    for c, why in VDEM_SKIP.items():
        anomalie("info", "VDEM_NON_RAPPROCHE", why, c, "C4")
    VDEM_URL = "https://www.v-dem.net/data/the-v-dem-dataset/"
    for iso3, (y, v) in sorted(vd.items()):
        add("C4", iso3, v, y, "V-Dem Institute – V-Dem Country-Year Full+Others (vdemdata 16.0), v2clstown", VDEM_URL, "vdem_extrait.csv",
            "variable v2clstown_osp (estimation du modèle de mesure ramenée à l'échelle d'origine 0-4) ; dernière année de la fenêtre ; reprise telle quelle",
            limites="Notation d'experts agrégée par modèle de mesure (V-Dem) ; incertitude publiée (codelow/codehigh)", alt=True)

# Freedom House
FH_SRC = "Freedom House – Freedom in the World 2024"
FH_URL = "https://freedomhouse.org/report/freedom-world"
for iso3, d in fh_by_iso.items():
    lim = "Notation d'experts d'une ONG ; édition 2024 = événements de l'année civile 2023"
    for ind_id, col in (("A6", "G2"), ("D3", "D"), ("D4", "E")):
        if d.get(col) is not None:
            add(ind_id, iso3, float(d[col]), FH_EDITION - 1, IND_BY_ID[ind_id]["source"], FH_URL, "freedomhouse_fiw_2013-2024.xlsx", f"colonne {col} reprise telle quelle", limites=lim)
    if d.get("PR") is not None:
        add("D2", iso3, float(d["PR"]), FH_EDITION - 1, IND_BY_ID["D2"]["source"], FH_URL, "freedomhouse_fiw_2013-2024.xlsx", "colonne PR (A+B+C) reprise telle quelle", limites=lim)
    elif all(d.get(k) is not None for k in "ABC"):
        add("D2", iso3, float(d["A"] + d["B"] + d["C"]), FH_EDITION - 1, IND_BY_ID["D2"]["source"], FH_URL, "freedomhouse_fiw_2013-2024.xlsx", "A+B+C", limites=lim)

# ------------------------------------------------------------------ contrôles de cohérence
seen = set()
for o in obs:
    k = (o["iso3"], o["indicateur"])
    if k in seen:
        anomalie("erreur", "DOUBLON", "observation en double", *k)
    seen.add(k)
# valeurs extrêmes (écart à la médiane > 5 MAD) : conservées mais signalées
by_ind = {}
for o in obs:
    by_ind.setdefault(o["indicateur"], []).append(o)
for ind_id, lst in by_ind.items():
    vals = [o["valeur_brute"] for o in lst]
    if len(vals) < 8:
        continue
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) or 1e-9
    for o in lst:
        z = abs(o["valeur_brute"] - med) / (1.4826 * mad)
        if z > 5:
            o["statut_validation"] = "valide_avec_reserve"
            o["limites_comparabilite"] = (o["limites_comparabilite"] + " | valeur extrême (>5 MAD)").strip(" |")
            anomalie("avertissement", "VALEUR_EXTREME", f"valeur {o['valeur_brute']} ({round(z, 1)} MAD de la médiane {round(med, 3)})", o["iso3"], ind_id)
    for o in lst:
        if o["annee"] < 2021 and o["statut_validation"] == "valide":
            o["statut_validation"] = "valide_avec_reserve"
            o["limites_comparabilite"] = (o["limites_comparabilite"] + f" | donnée ancienne ({o['annee']})").strip(" |")

# ------------------------------------------------------------------ écriture
os.makedirs(OUT, exist_ok=True)


def write_csv(name, rows_, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows_:
            w.writerow(r)


write_csv("pays.csv", sorted(pays.values(), key=lambda p: p["iso3"]),
          ["iso3", "iso2", "nom_fr", "nom_en", "region", "groupe_revenu", "type", "statut_politique", "origine_referentiel"])
OF = ["iso3", "indicateur", "valeur_brute", "unite", "annee", "source", "url_source", "date_collecte", "date_revision",
      "transformation", "statut_validation", "limites_comparabilite", "fichier_brut"]
write_csv("observations.csv", sorted(obs, key=lambda o: (o["indicateur"], o["iso3"])), OF)
write_csv("indicateurs_alt.csv", sorted(obs_alt, key=lambda o: (o["indicateur"], o["iso3"])), OF)
write_csv("anomalies.csv", anomalies, ["niveau", "code", "iso3", "indicateur", "detail"])

cov = {i: len(v) for i, v in sorted(by_ind.items())}
print("pays/territoires :", len(pays), "| observations :", len(obs), "| alternatives :", len(obs_alt), "| anomalies :", len(anomalies))
print("couverture par indicateur :", cov)
