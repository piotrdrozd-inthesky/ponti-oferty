#!/usr/bin/env python3
"""Przepisuje dane z repozytorium do folderu BAZA WIEDZY na Dysku Google.

    python3 tools/synchronizuj_baze.py

BAZA WIEDZY ma byc jedynym zrodlem prawdy o PONTI, a `baza_wiedzy.json` zasila
asystenta czatu. Od 29.07.2026 tresc mieszka w tym repozytorium, wiec kopia
na Dysku musi z niego wynikac - inaczej za tydzien beda dwie wersje prawdy.

Skrypt nie rusza plikow .md - te opisuja decyzje i pisze je czlowiek.
"""
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_kand = glob.glob("/Users/piotrdrozd/Library/CloudStorage/"
                  "GoogleDrive-*/Dyski*/PONTI*/OFERTY/BAZA WIEDZY")
if not _kand:
    sys.exit("Nie znalazlem folderu BAZA WIEDZY na Dysku Google.")
BW = _kand[0]


def main():
    baza = json.load(open(os.path.join(REPO, "data", "baza.json"), encoding="utf-8"))
    asy = json.load(open(os.path.join(REPO, "data", "asystent.json"), encoding="utf-8"))

    zrodlo = ("Plik generowany z repozytorium ponti-oferty przez "
              "tools/synchronizuj_baze.py. Nie edytuj recznie - zmien "
              "data/baza.json albo data/asystent.json i uruchom skrypt ponownie.")

    scalone = {
        "_zrodlo": zrodlo,
        "_aktualizacja": baza["_aktualizacja"],
        "firma": baza["firma"],
        "pojemnosc": baza["pojemnosc"],
        "sale": baza["sale"],
        "menu_progi": baza["menu_progi"],
        "wellness": baza["wellness"],
        "wydarzenia": [
            {k: v for k, v in w.items()
             if k in ("id", "label", "label_dl", "od", "typowo", "termin", "czas",
                      "menu", "sala", "bez_typowego")}
            for w in baza["wydarzenia"]
        ],
        "dodatki": baza["dodatki"],
        "minimum": baza["minimum"],
        "prowizja": baza["prowizja"],
        "rzemieslnicy": baza["rzemieslnicy"],
        "karta_ceny": baza["karta_ceny"],
        "asystent": {
            "powitanie": asy["powitanie_baza"],
            "niewiem": asy["niewiem"],
            "mocne": asy["mocne"],
            "intencje": asy["intencje"],
            "wg_okazji": asy["wg_okazji"],
        },
    }

    cel = os.path.join(BW, "baza_wiedzy.json")
    json.dump(scalone, open(cel, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("zapisane: %s (%.1f kB)" % (cel, os.path.getsize(cel) / 1024))
    print("  %d typow wydarzen, %d intencji asystenta, telefon %s"
          % (len(scalone["wydarzenia"]), len(asy["intencje"]),
             baza["firma"]["telefon"]))


if __name__ == "__main__":
    main()
