#!/usr/bin/env python3
"""Initialise (ou complète) le référentiel géographique et la table de correspondance des sources.

À exécuter seulement lors de l'ajout d'une source ou d'une édition ; le résultat est relu puis versionné.
La construction des données (src/build.py) ne fait AUCUN rapprochement automatique : elle lit uniquement
data/reference/correspondances.csv et échoue si une entité source n'y figure pas.

Méthodes de rapprochement enregistrées dans la colonne « methode » :
  code_identique  – code V-Dem (country_text_id) identique à l'ISO3 du référentiel ET noms concordants vérifiés à la main
  nom_identique   – nom de la source identique (après normalisation casse/accents/ponctuation) au nom anglais Banque mondiale
  manuel          – rapprochement explicite listé ci-dessous (à relire en cas de nouvelle édition)
"""
import csv
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common import RAW, REF, read_csv, write_csv  # noqa: E402

PAYS_FIELDS = ["iso3", "iso2", "nom_fr", "nom_en", "region", "groupe_revenu", "type", "statut_politique", "origine_referentiel"]
CORR_FIELDS = ["source", "edition", "nom_source", "code_source", "iso3", "methode", "note"]

# Régions des territoires sans région Banque mondiale : région BM de l'État de rattachement ou de contrôle de jure
REGION_RATTACHEMENT = {
    "X-ABK": "GEO", "X-OSS": "GEO", "X-CRM": "UKR", "X-DON": "UKR", "X-RUA": "UKR", "X-TRN": "MDA", "X-ESH": "MAR",
    "X-GAZ": "PSE", "X-WBK": "PSE", "X-KAI": "IND", "X-KAP": "PAK", "X-NCY": "CYP", "X-NKR": "AZE", "X-SML": "SOM",
    "X-TIB": "CHN", "X-ZZB": "TZA", "TWN": "CHN",
}
AJOUTS = [  # entités absentes du référentiel V1
    {"iso3": "X-RUA", "iso2": "", "nom_fr": "Territoires ukrainiens occupés par la Russie", "nom_en": "Russian-occupied territories of Ukraine",
     "type": "territoire", "groupe_revenu": "Non classé", "origine_referentiel": "Freedom House (FIW 2026)",
     "statut_politique": "Territoires d'Ukraine sous occupation russe ; entité introduite par Freedom House dans l'édition 2026, qui ne publie plus séparément la Crimée et le Donbass oriental (frontière de l'entité différente des éditions antérieures)"},
    {"iso3": "X-ZZB", "iso2": "", "nom_fr": "Zanzibar", "nom_en": "Zanzibar", "type": "territoire", "groupe_revenu": "Non classé",
     "origine_referentiel": "V-Dem", "statut_politique": "Région semi-autonome de la République-Unie de Tanzanie (codée séparément par V-Dem)"},
]
MANUEL = {
    ("fraser", "Côte d’Ivoire"): "CIV", ("fraser", "Somalia"): "SOM", ("fraser", "Vietnam"): "VNM",
    ("heritage", "Burma"): "MMR", ("heritage", "Czech Republic"): "CZE", ("heritage", "Côte d’Ivoire"): "CIV",
    ("heritage", "Democratic Republic of Congo"): "COD", ("heritage", "Egypt"): "EGY", ("heritage", "Iran"): "IRN",
    ("heritage", "Laos"): "LAO", ("heritage", "Micronesia"): "FSM", ("heritage", "North Korea"): "PRK",
    ("heritage", "Republic of Congo"): "COG", ("heritage", "Russia"): "RUS", ("heritage", "Saint Lucia"): "LCA",
    ("heritage", "Saint Vincent and the Grenadines"): "VCT", ("heritage", "Slovakia"): "SVK", ("heritage", "Somalia"): "SOM",
    ("heritage", "South Korea"): "KOR", ("heritage", "Syria"): "SYR", ("heritage", "The Bahamas"): "BHS",
    ("heritage", "The Gambia"): "GMB", ("heritage", "The Netherlands"): "NLD", ("heritage", "Venezuela"): "VEN",
    ("heritage", "Vietnam"): "VNM", ("heritage", "Yemen"): "YEM",
    ("freedomhouse", "Bahamas"): "BHS", ("freedomhouse", "The Bahamas"): "BHS", ("freedomhouse", "Brunei"): "BRN",
    ("freedomhouse", "Congo (Brazzaville)"): "COG", ("freedomhouse", "Republic of the Congo"): "COG",
    ("freedomhouse", "Congo (Kinshasa)"): "COD", ("freedomhouse", "Democratic Republic of the Congo"): "COD",
    ("freedomhouse", "Czech Republic"): "CZE", ("freedomhouse", "Egypt"): "EGY", ("freedomhouse", "Hong Kong"): "HKG",
    ("freedomhouse", "Iran"): "IRN", ("freedomhouse", "Kyrgyzstan"): "KGZ", ("freedomhouse", "Laos"): "LAO",
    ("freedomhouse", "Micronesia"): "FSM", ("freedomhouse", "Nauru"): "NRU", ("freedomhouse", "North Korea"): "PRK",
    ("freedomhouse", "Puerto Rico"): "PRI", ("freedomhouse", "Russia"): "RUS", ("freedomhouse", "Slovakia"): "SVK",
    ("freedomhouse", "Somalia"): "SOM", ("freedomhouse", "South Korea"): "KOR", ("freedomhouse", "Syria"): "SYR",
    ("freedomhouse", "The Gambia"): "GMB", ("freedomhouse", "Turkey"): "TUR", ("freedomhouse", "Venezuela"): "VEN",
    ("freedomhouse", "Vietnam"): "VNM", ("freedomhouse", "Yemen"): "YEM",
    ("freedomhouse", "Russian-occupied territories of Ukraine"): "X-RUA",
    ("vdem", "PSE"): "X-WBK", ("vdem", "PSG"): "X-GAZ", ("vdem", "SML"): "X-SML", ("vdem", "ZZB"): "X-ZZB",
}
NOTES = {("vdem", "PSE"): "V-Dem « Palestine/West Bank » = Cisjordanie seule ; le code ISO PSE du référentiel désigne Cisjordanie + Gaza (Banque mondiale)",
         ("vdem", "PSG"): "V-Dem « Palestine/Gaza »", ("vdem", "SML"): "Somaliland codé séparément par V-Dem",
         ("freedomhouse", "Russian-occupied territories of Ukraine"): "entité FIW 2026 regroupant les territoires occupés (Crimée, Donbass…)"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main():
    base = os.path.join(REF, "pays.csv")
    pays = {p["iso3"]: p for p in read_csv(base if os.path.exists(base) else os.path.join(
        os.path.dirname(REF), "..", "archive", "v1", "data", "processed", "pays.csv"))}
    for a in AJOUTS:
        pays.setdefault(a["iso3"], {**a, "region": ""})
    for iso, parent in REGION_RATTACHEMENT.items():
        if iso in pays and parent in pays:
            pays[iso]["region"] = pays[parent]["region"]
    write_csv(base, sorted(pays.values(), key=lambda p: p["iso3"]), PAYS_FIELDS)

    by_name = {norm(p["nom_en"]): k for k, p in pays.items()}
    src_names = {
        ("fraser", "efw2025"): sorted({r["nom_source"] for r in read_csv(os.path.join(RAW, "fraser", "efw2025_extraction.csv"))}),
        ("heritage", "ief2026"): sorted({r["nom_source"] for r in read_csv(os.path.join(RAW, "heritage", "ief2026_extraction.csv"))}),
        ("freedomhouse", "fiw2026"): sorted({r["nom_source"] for r in read_csv(os.path.join(RAW, "freedomhouse", "fiw2026_extraction.csv"))}),
        ("freedomhouse", "fiw2013_2024"): sorted({r["nom_source"] for r in read_csv(os.path.join(RAW, "freedomhouse", "fiw2013_2024_extraction.csv"))}),
    }
    rows, missing = [], []
    for (src, ed), names in src_names.items():
        for n in names:
            if (src, n) in MANUEL:
                iso, meth = MANUEL[(src, n)], "manuel"
            elif norm(n) in by_name:
                iso, meth = by_name[norm(n)], "nom_identique"
            else:
                missing.append((src, ed, n))
                continue
            rows.append({"source": src, "edition": ed, "nom_source": n, "code_source": "", "iso3": iso, "methode": meth,
                         "note": NOTES.get((src, n), "")})
    vd = {}
    for r in read_csv(os.path.join(RAW, "vdem", "vdem_v16_extraction.csv")):
        vd[r["country_text_id"]] = r["country_name"]
    for code, n in sorted(vd.items()):
        if ("vdem", code) in MANUEL:
            iso, meth = MANUEL[("vdem", code)], "manuel"
        elif code in pays:
            iso, meth = code, "code_identique"
        else:
            missing.append(("vdem", "v16", code))
            continue
        rows.append({"source": "vdem", "edition": "v16", "nom_source": n, "code_source": code, "iso3": iso, "methode": meth,
                     "note": NOTES.get(("vdem", code), "")})
    for r in rows:
        assert r["iso3"] in pays, r
    write_csv(os.path.join(REF, "correspondances.csv"), rows, CORR_FIELDS)
    print(len(pays), "entités ;", len(rows), "correspondances ; non rapprochées :", missing)
    return missing


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
