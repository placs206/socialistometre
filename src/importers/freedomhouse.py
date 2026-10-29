"""Extraction littérale des scores Freedom in the World (Freedom House).

- FIW 2026 (année 2025) : tableau HTML officiel « Global Freedom Scores » (https://freedomhouse.org/countries/freedom-world/scores).
  Chaque ligne : nom (astérisque = territoire), score total /100, statut, droits politiques, libertés civiles ; le lien
  « /freedom-world/2026 » de chaque ligne confirme l'édition.
- FIW 2013-2024 (années 2012-2023) : classeur officiel « All_data_FIW_2013-2024.xlsx », colonnes PR, CL, Total, Status.
"""
import html
import os
import re

import openpyxl

from src.common import DL, RAW, write_csv

FIELDS = ["edition", "nom_source", "type_source", "annee", "total", "pr", "cl", "statut", "url_fiche", "origine"]
STATUS = {"free": "Libre (F)", "partly-free": "Partiellement libre (PF)", "not-free": "Non libre (NF)",
          "F": "Libre (F)", "PF": "Partiellement libre (PF)", "NF": "Non libre (NF)"}


def _cell(td):
    m = re.search(r'<span class="score[^"]*">([^<]*)</span>', td)
    return m.group(1).strip() if m else ""


def extract_2026():
    h = open(os.path.join(RAW, "freedomhouse", DL, "fiw2026_scores.html"), encoding="utf-8").read()
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        if 'data-code="country_name"' not in tr or '<td' not in tr:
            continue
        name_m = re.search(r'data-code="country_name"><a href="(/country/[^"]+)">([^<]+)</a>', tr)
        fiw_td = re.search(r'data-code="fiw">(.*?)</td>', tr, re.S).group(1)
        if "not-covered" in fiw_td or "Not covered" in fiw_td:
            continue  # ex. Antarctique : non couvert par FIW
        link = re.search(r'href="(/country/[^"]+/freedom-world/(\d{4}))"', fiw_td)
        assert link and link.group(2) == "2026", tr[:300]
        total = re.search(r'<span class="score">(-?\d+)</span>/<span class="score-maximum">100</span>', fiw_td).group(1)
        st = re.search(r'class="status status-([a-z-]+)"', fiw_td).group(1)
        pr = _cell(re.search(r'data-code="fiw-pr">(.*?)</td>', tr, re.S).group(1))
        cl = _cell(re.search(r'data-code="fiw-cl">(.*?)</td>', tr, re.S).group(1))
        raw_name = html.unescape(name_m.group(2)).strip()
        rows.append({"edition": "fiw2026", "nom_source": raw_name.rstrip("*").strip(),
                     "type_source": "territoire" if raw_name.endswith("*") else "pays", "annee": 2025, "total": total,
                     "pr": pr, "cl": cl, "statut": STATUS[st], "url_fiche": "https://freedomhouse.org" + link.group(1),
                     "origine": "page « Global Freedom Scores »"})
    return rows


def extract_2013_2024():
    wb = openpyxl.load_workbook(os.path.join(RAW, "freedomhouse", "freedomhouse_fiw_2013-2024.xlsx"), read_only=True, data_only=True)
    rows = list(wb["FIW13-24"].iter_rows(values_only=True))
    hdr = list(rows[1])
    ix = {k: hdr.index(k) for k in ("Country/Territory", "C/T", "Edition", "Status", "PR", "CL", "Total")}
    out = []
    for r in rows[2:]:
        if not r[ix["Country/Territory"]]:
            continue
        ed = int(r[ix["Edition"]])
        out.append({"edition": "fiw2013_2024", "nom_source": str(r[ix["Country/Territory"]]).strip(),
                    "type_source": "territoire" if r[ix["C/T"]] == "t" else "pays", "annee": ed - 1, "total": r[ix["Total"]],
                    "pr": r[ix["PR"]], "cl": r[ix["CL"]], "statut": STATUS.get(r[ix["Status"]], r[ix["Status"]]),
                    "url_fiche": "", "origine": f"All_data_FIW_2013-2024.xlsx, feuille FIW13-24, édition {ed}"})
    return out


def run():
    a, b = extract_2026(), extract_2013_2024()
    write_csv(os.path.join(RAW, "freedomhouse", "fiw2026_extraction.csv"), a, FIELDS)
    write_csv(os.path.join(RAW, "freedomhouse", "fiw2013_2024_extraction.csv"), b, FIELDS)
    return a, b
