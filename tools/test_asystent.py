#!/usr/bin/env python3
"""Sprawdza, czy asystent trafia w wlasciwe tematy.

Powtarza w Pythonie doklad­nie te sama logike dopasowania, ktora siedzi w HTML,
i uruchamia ja na dwoch zestawach:

  1. Etykiety przyciskow podpowiedzi - kazda MUSI wrocic do swojej intencji.
     Inaczej gosc klika "Sala Onda", a asystent opowiada o czym innym.
  2. Prawdziwe pytania, jakie zadaja goscie - do przejrzenia okiem.

Uruchomienie: python3 tools/test_asystent.py
"""
import json
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from buduj import TEMATY, wczytaj  # noqa: E402

MAPA = {"ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o",
        "ś": "s", "ż": "z", "ź": "z"}


def norm(s):
    s = (s or "").lower()
    for a, b in MAPA.items():
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match(q, intencje):
    n = " " + norm(q) + " "
    best = None
    best_sc = 0
    best_ev = None
    best_ev_sc = 0
    for it in intencje:
        sc = 0
        for k in it["kw"]:
            kn = norm(k)
            if not kn:
                continue
            if (" " + kn + " ") in n:
                sc += len(kn.split()) * 3
            elif kn in n:
                sc += len(kn.split()) * 2
        if sc <= 0:
            continue
        if it["id"].endswith("_q") and sc > best_ev_sc:
            best_ev_sc, best_ev = sc, it
        if sc > best_sc:
            best_sc, best = sc, it
    if best_ev and best_ev_sc >= 3 and best_sc <= best_ev_sc * 3:
        return best_ev
    return best if best_sc >= 2 else None


# Pytania, ktore realnie padaja. Oczekiwanie = id intencji albo None.
PYTANIA = [
    ("dzien dobry", "powitanie"),
    ("ile kosztuje komunia dla 30 osob", "komunia_q"),
    ("czy macie sale na 40 osob", "ile_osob"),
    ("ile kosztuje jacuzzi", "wellness_strefa"),
    ("czy jest sauna", "wellness_strefa"),
    ("chcemy wynajac cala restauracje", "wylacznosc"),
    ("co to sala onda", "sala_onda"),
    ("czy mozna u was przenocowac", "nocleg"),
    ("szkolenie dla 25 osob z lunchem", "konferencja_q"),
    ("romantyczna kolacja we dwoje", "para_q"),
    ("ile za masaz dla dwojga", "wellness_zabiegi"),
    ("czy dostane fakture", "zaliczka"),
    ("czy doliczacie oplate serwisowa", "zaliczka"),
    ("do ktorej jestescie otwarci", "godziny"),
    ("czy robicie sniadania", "godziny"),
    ("czy mozna przyjsc z psem", "pies"),
    ("mam alergie na gluten", "dieta"),
    ("skad bierzecie sery", "rzemieslnicy"),
    ("czy moge przyniesc wlasna wodke", "korkowe"),
    ("gdzie zaparkowac", "parking"),
    ("chce zarezerwowac termin na wrzesien", "termin"),
    ("czy jest voucher na prezent", "wellness_voucher"),
    ("grupa przyjezdza z warszawy na dwa dni", "kompleks_q"),
    ("ile kosztuje wieczor panienski", "panienskie_q"),
    ("jakie macie makarony", "kuchnia"),
    ("czy sa dania dla dzieci", "dzieci"),
    ("chcemy tort z wlasnej cukierni", "tort"),
    ("czy macie dj", "muzyka"),
    ("jaki jest numer telefonu", "kontakt"),
    ("czy da sie zjesc na tarasie", "widok_taras"),
    # pytania poza baza - asystent ma sie przyznac, ze nie wie
    ("czy macie miejsce do przewijania niemowlaka", None),
    ("jaki jest kod do wifi", None),
]


def main():
    asy = wczytaj("asystent.json")
    intencje = [{
        "id": "powitanie",
        "kw": ["czesc", "hej", "dzien dobry", "witam", "halo", "siema", "dobry wieczor"],
        "a": asy["powitanie_baza"], "s": 0,
        "nast": ["cena_ogolna", "ile_osob", "wellness_strefa"],
    }] + asy["intencje"]

    bledy = 0

    print("== Etykiety przyciskow (kazda musi wrocic do swojej intencji) ==")
    for ident, etykieta in TEMATY.items():
        hit = match(etykieta, intencje)
        got = hit["id"] if hit else None
        if got != ident:
            print("  BLAD  %-22s -> %-22s (etykieta: %r)" % (ident, got, etykieta))
            bledy += 1
    print("  sprawdzonych: %d, bledow: %d" % (len(TEMATY), bledy))

    print("\n== Prawdziwe pytania ==")
    zle = 0
    for q, oczekiwane in PYTANIA:
        hit = match(q, intencje)
        got = hit["id"] if hit else None
        znak = "ok  " if got == oczekiwane else "ZLE "
        if got != oczekiwane:
            zle += 1
        print("  %s %-46s -> %-20s (oczekiwane: %s)" % (znak, q, got, oczekiwane))
    print("  pytan: %d, niezgodnych: %d" % (len(PYTANIA), zle))

    # pokrycie: ile intencji ma sensowne nastepne pytania
    bez_nast = [i["id"] for i in intencje if not i.get("nast")]
    if bez_nast:
        print("\nIntencje bez podpowiedzi 'nast': %s" % ", ".join(bez_nast))

    print("\nRAZEM: %d intencji w bazie asystenta" % len(intencje))
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
