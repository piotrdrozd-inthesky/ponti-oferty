#!/usr/bin/env python3
"""Wyciaga zdjecia base64 z ofert PONTI do osobnych plikow WebP.

Zrodlo: PONTI MATERIALY / OFERTY (Dysk Google) - pliki 4 MB z zdjeciami w kodzie.
Wynik:  assets/img/*.webp + HTML ze sciezkami relatywnymi.

Uruchomienie: python3 tools/wyodrebnij_zdjecia.py
"""
import base64
import hashlib
import os
import re
import subprocess
import sys
import unicodedata

import glob

# Folder OFERTY na Dysku Google. Nazwy katalogow maja polskie znaki, wiec
# szukamy ich wzorcem zamiast wpisywac na sztywno.
_kandydaci = glob.glob("/Users/piotrdrozd/Library/CloudStorage/"
                       "GoogleDrive-*/Dyski*/PONTI*/OFERTY")
if not _kandydaci:
    sys.exit("Nie znalazlem folderu OFERTY na Dysku Google.")
ZRODLO = _kandydaci[0]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(REPO, "assets", "img")
TMP = os.path.join(REPO, ".tmp-img")

PLIKI = {
    "PONTI_Prezentacja_dla_Gosci.html": "goscie.html",
    "PONTI_Oferta_Partnerska.html": "partnerska.html",
    "PONTI_Voucher_Landing.html": "voucher.html",
}

# alt/nazwa -> stabilny slug pliku; reszta dostaje nazwe z hasha
RE_DATA = re.compile(r'data:image/([a-z]+);base64,([A-Za-z0-9+/=]+)')


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:48] or "foto"


def kontekst(html, poz):
    """Nazwa dla zdjecia na podstawie alt= albo klasy w okolicy wystapienia."""
    okno = html[max(0, poz - 400):poz + 400]
    m = re.search(r'alt="([^"]{2,60})"', okno)
    if m:
        return slug(m.group(1))
    m = re.search(r'class="([a-z0-9 _-]{2,40})"', okno)
    if m:
        return slug(m.group(1).split()[0])
    return "foto"


def main():
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    mapa = {}      # md5 -> nazwa pliku webp
    uzyte = set()
    laczna_przed = 0
    laczna_po = 0

    for zrodlowy, docelowy in PLIKI.items():
        sciezka = os.path.join(ZRODLO, zrodlowy)
        if not os.path.exists(sciezka):
            sys.exit("Brak pliku: " + sciezka)
        html = open(sciezka, encoding="utf-8", errors="replace").read()

        wynik = []
        ostatni = 0
        for m in RE_DATA.finditer(html):
            ext, b64 = m.group(1), m.group(2)
            surowe = base64.b64decode(b64)
            h = hashlib.md5(surowe).hexdigest()
            laczna_przed += len(surowe)

            if h not in mapa:
                baza = kontekst(html, m.start())
                nazwa = baza
                i = 2
                while nazwa in uzyte:
                    nazwa = "%s-%d" % (baza, i)
                    i += 1
                uzyte.add(nazwa)

                tmp = os.path.join(TMP, nazwa + "." + ext)
                open(tmp, "wb").write(surowe)
                cel = os.path.join(IMG, nazwa + ".webp")
                # -resize 0 1800: przycina tylko wysokosc jesli wieksza; szerokosc proporcjonalnie
                subprocess.run(
                    ["cwebp", "-q", "80", "-m", "6", "-metadata", "none",
                     "-resize", "1800", "0", tmp, "-o", cel],
                    check=False, capture_output=True)
                if not os.path.exists(cel) or os.path.getsize(cel) == 0:
                    # zdjecie wezsze niz 1800 px - konwersja bez skalowania
                    subprocess.run(["cwebp", "-q", "80", "-m", "6",
                                    "-metadata", "none", tmp, "-o", cel],
                                   check=True, capture_output=True)
                mapa[h] = nazwa + ".webp"
                laczna_po += os.path.getsize(cel)

            wynik.append(html[ostatni:m.start()])
            wynik.append("assets/img/" + mapa[h])
            ostatni = m.end()
        wynik.append(html[ostatni:])

        out = os.path.join(REPO, docelowy)
        open(out, "w", encoding="utf-8").write("".join(wynik))
        print("%-38s -> %-16s %6.2f MB -> %6.2f MB"
              % (zrodlowy, docelowy,
                 len(html) / 1048576, os.path.getsize(out) / 1048576))

    print("\nZdjec unikalnych: %d" % len(mapa))
    print("Waga zdjec: %.2f MB -> %.2f MB (WebP q80, max 1800 px)"
          % (laczna_przed / 1048576, laczna_po / 1048576))
    for h, n in sorted(mapa.items(), key=lambda x: x[1]):
        print("  %s  %6.0f kB" % (n, os.path.getsize(os.path.join(IMG, n)) / 1024))


if __name__ == "__main__":
    main()
