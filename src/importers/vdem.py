"""Extrait littéral du jeu V-Dem v16 (country-year) : indice de démocratie libérale et composantes officielles.

Lecture de data/vdem.RData du paquet officiel « vdemdata » 16.0 (V-Dem Institute) avec pyreadr.
Années conservées : 2000-2025 (mode historique). Les valeurs sont recopiées sans arrondi supplémentaire.
Licence de l'extrait : CC BY-SA 4.0 (identique à la source).
"""
import os

from src.common import DL, RAW, write_csv

VARS = ["v2x_libdem", "v2x_libdem_codelow", "v2x_libdem_codehigh", "v2x_libdem_sd", "v2x_polyarchy", "v2x_liberal"]
FIELDS = ["edition", "country_name", "country_text_id", "country_id", "year"] + VARS
Y0 = 2000


def _fmt(v):
    if v is None or v != v:  # NaN
        return ""
    return repr(float(v))


def run():
    import pyreadr
    d = os.path.join(RAW, "vdem", DL, "vdemdata")
    df = pyreadr.read_r(os.path.join(d, "data", "vdem.RData"))["vdem"]
    df = df[df["year"] >= Y0]
    rows = []
    for r in df[["country_name", "country_text_id", "country_id", "year"] + VARS].itertuples(index=False):
        r = r._asdict()
        rows.append({"edition": "v16", "country_name": r["country_name"], "country_text_id": r["country_text_id"],
                     "country_id": int(r["country_id"]), "year": int(r["year"]), **{v: _fmt(r[v]) for v in VARS}})
    rows.sort(key=lambda x: (x["country_text_id"], x["year"]))
    write_csv(os.path.join(RAW, "vdem", "vdem_v16_extraction.csv"), rows, FIELDS)
    return rows
