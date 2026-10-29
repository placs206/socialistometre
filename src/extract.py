#!/usr/bin/env python3
"""Ré-extrait les valeurs officielles des fichiers sources téléchargés (data/raw/*/_telechargements/) vers les CSV
d'extraction littérale versionnés. À lancer après tools/collect.py. Usage : python3 -m src.extract"""
from src.importers import fraser, freedomhouse, heritage, vdem

if __name__ == "__main__":
    print("fraser", len(fraser.run()))
    print("heritage", len(heritage.run()))
    a, b = freedomhouse.run(); print("freedomhouse", len(a), len(b))
    print("vdem", len(vdem.run()))
