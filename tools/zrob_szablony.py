#!/usr/bin/env python3
"""Jednorazowa konwersja: HTML z Dysku -> szablony + wspolny CSS.

Wycina z gotowych plikow HTML te fragmenty, ktore powtarzaja sie dla kazdego
typu wydarzenia, i zastepuje je znacznikami {{NAZWA}}. Od tej pory tresc bierze
sie z data/*.json, a strony sklada tools/buduj.py.

CSS wychodzi do assets/<strona>.css, zeby przegladarka mogla go zacacheowac
i zeby dalo sie na niego nalozyc warstwe assets/lift.css.

Uruchomienie: python3 tools/zrob_szablony.py
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SZAB = os.path.join(REPO, "szablony")
CSS = os.path.join(REPO, "assets")

# strona -> (nazwa_css, [(od, do, znacznik, wzorzec_pierwszej_linii)])
# Numery linii z plikow wyjsciowych skryptu wyodrebnij_zdjecia.py (1-indexed).
PLAN = {
    "goscie.html": {
        "css": (10, 507),
        "regiony": [
            (519, 548, "CHOOSER", r'<button class="ch-card" data-pick="chrzciny">'),
            (676, 764, "OKAZJE", r'<div class="band rv" data-ev-band="chrzciny">'),
            (882, 1049, "CENY_OKAZJE", r'<div class="pr-hero rev" data-ev-price="chrzciny">'),
            (1056, 1077, "CENY_PROGI", r'<div class="pr-tiers">'),
            (1079, 1082, "CENY_ZAUFANIE", r'<div class="pr-trust rev">'),
            (1085, 1092, "CENY_MINIMUM", r'<div class="pr-min rev">'),
            (1107, 1197, "PAKIETY", r'<div class="pk-cols rv d1">'),
            (1235, 1244, "FAKTY", r'<div class="facts rv d1">'),
            (1289, 1290, "EV_CFG", r'var EV_COPY = '),
            (1417, 1417, "KB", r'var KB = '),
        ],
    },
    "partnerska.html": {
        "css": (10, 505),
        "regiony": [
            (519, 549, "CHOOSER", r'<button class="ch-card" data-pick="chrzciny">'),
            (786, 791, "TABS", r'<button class="tab on" data-t="chrzciny">'),
            (795, 878, "PANES", r'<div class="pane on" data-p="chrzciny">'),
            (895, 1062, "CENY_OKAZJE", r'<div class="pr-hero rev" data-ev-price="chrzciny">'),
            (1069, 1090, "CENY_PROGI", r'<div class="pr-tiers">'),
            (1092, 1095, "CENY_ZAUFANIE", r'<div class="pr-trust rev">'),
            (1098, 1106, "CENY_MINIMUM", r'<div class="pr-min rev">'),
            (1120, 1205, "PAKIETY", r'<div class="pk-grid">'),
            (1352, 1352, "EV_CFG", r'var EV_LABEL = '),
        ],
    },
}


def konwertuj(plik, plan):
    # Szablony sa potem dopracowywane recznie - nie wolno ich nadpisac.
    if os.path.exists(os.path.join(SZAB, plik)):
        print("%-18s pomijam, szablon juz istnieje" % plik)
        return
    sciezka = os.path.join(REPO, plik)
    linie = open(sciezka, encoding="utf-8").read().split("\n")

    # CSS na zewnatrz
    c_od, c_do = plan["css"]
    if "<style>" not in linie[c_od - 1]:
        sys.exit("%s: linia %d to nie <style>, a %r" % (plik, c_od, linie[c_od - 1][:60]))
    if "</style>" not in linie[c_do - 1]:
        sys.exit("%s: linia %d to nie </style>" % (plik, c_do))
    css = "\n".join(linie[c_od:c_do - 1])
    nazwa_css = plik.replace(".html", ".css")
    open(os.path.join(CSS, nazwa_css), "w", encoding="utf-8").write(css.strip() + "\n")

    podmiany = [(c_od, c_do,
                 '<link rel="stylesheet" href="assets/%s">\n'
                 '<link rel="stylesheet" href="assets/lift.css">' % nazwa_css)]

    for od, do, znacznik, wzor in plan["regiony"]:
        pierwsza = linie[od - 1]
        if not re.search(wzor, pierwsza):
            sys.exit("%s: linia %d nie pasuje do %s\n  jest: %r"
                     % (plik, od, znacznik, pierwsza[:90]))
        podmiany.append((od, do, "{{%s}}" % znacznik))

    # od konca, zeby numery linii sie nie przesuwaly
    podmiany.sort(reverse=True)
    for od, do, tekst in podmiany:
        linie[od - 1:do] = [tekst]

    wynik = "\n".join(linie)
    open(os.path.join(SZAB, plik), "w", encoding="utf-8").write(wynik)
    print("%-18s -> szablony/%s  (%d linii, CSS %d linii)"
          % (plik, plik, wynik.count("\n"), css.count("\n")))


if __name__ == "__main__":
    os.makedirs(SZAB, exist_ok=True)
    for plik, plan in PLAN.items():
        konwertuj(plik, plan)
