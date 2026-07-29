#!/usr/bin/env python3
"""Porzadkuje biblioteke zdjec PONTI.

1. Zmienia nazwy plikow wyciagnietych z base64 na opisowe (nazwy z klas CSS
   nic nie mowily) i poprawia sciezki w HTML.
2. Dokłada zdjecia, ktorych w ofertach nie bylo: Sala Onda, apartamenty,
   strefa wellness w dzien, gabinet masazu, szyld.

Skrypt jest idempotentny - drugie uruchomienie nic nie psuje.
"""
import glob
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(REPO, "assets", "img")
HTML = ["goscie.html", "partnerska.html", "voucher.html"]

# stara nazwa -> nowa nazwa (co faktycznie jest na zdjeciu)
ZMIANY = {
    "hdot": "sala-okno-taras",
    "lede": "sala-glowna",
    "band": "lounge",
    "band-2": "dlugi-stol",
    "band-3": "zielony-salon",
    "mf-sign": "szef-kuchni",
    "mrow": "ravioli",
    "pstrag": "rigatoni",
    "ravioli-duo": "tagliata",
    "tagliata": "pstrag",
    "sala-i-bar": "taras-wieczorem",
    "v-why": "jacuzzi-wieczor",
    "v-why-2": "gabinet-vichy",
}

_dysk = glob.glob("/Users/piotrdrozd/Library/CloudStorage/"
                  "GoogleDrive-*/Dyski*/PONTI*")
if not _dysk:
    sys.exit("Nie znalazlem folderu PONTI MATERIALY na Dysku Google.")
B = _dysk[0]

# nowa nazwa -> sciezka zrodlowa na Dysku
DOLOZ = {
    "sala-onda": B + "/DLA CHATGPT DO OFERT/KONFERENCJE/Onda1.HEIC",
    "apart-sypialnia": B + "/DLA CHATGPT DO OFERT/HOTEL/Kopia Sypialnia-506.jpg",
    "apart-salon": B + "/DLA CHATGPT DO OFERT/HOTEL/Kopia Salon+Kuchnia-506.jpg",
    "jacuzzi-dzien": B + "/OFERTY/_foto_jacuzzi_dzien2.png",
    "gabinet-masaz": B + "/SPA/WNETRZE/8.png",
    "szyld": B + "/DLA CHATGPT DO OFERT/RESTAURACJA/Szyld.JPG",
}
# SPA/WNETRZE ma polski znak w nazwie
DOLOZ["gabinet-masaz"] = glob.glob(B + "/SPA/WN*/8.png")[0] \
    if glob.glob(B + "/SPA/WN*/8.png") else DOLOZ["gabinet-masaz"]


def zmien_nazwy():
    # dwa przejscia, bo nowe nazwy koliduja ze starymi (tagliata <-> pstrag)
    for stara, nowa in ZMIANY.items():
        s = os.path.join(IMG, stara + ".webp")
        if os.path.exists(s):
            os.rename(s, os.path.join(IMG, "_tmp_" + nowa + ".webp"))
    for nowa in ZMIANY.values():
        t = os.path.join(IMG, "_tmp_" + nowa + ".webp")
        if os.path.exists(t):
            os.rename(t, os.path.join(IMG, nowa + ".webp"))
            print("  nazwa: %s" % nowa)

    for plik in HTML:
        p = os.path.join(REPO, plik)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        for stara, nowa in ZMIANY.items():
            t = t.replace("assets/img/%s.webp" % stara,
                          "assets/img/%s.webp" % nowa)
        open(p, "w", encoding="utf-8").write(t)


def doloz():
    tmp = os.path.join(REPO, ".tmp-img")
    os.makedirs(tmp, exist_ok=True)
    for nazwa, zrodlo in DOLOZ.items():
        cel = os.path.join(IMG, nazwa + ".webp")
        if os.path.exists(cel):
            continue
        if not os.path.exists(zrodlo):
            print("  BRAK zrodla: %s (%s)" % (nazwa, zrodlo))
            continue
        posr = os.path.join(tmp, nazwa + ".jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "1800",
                        zrodlo, "--out", posr],
                       check=True, capture_output=True)
        subprocess.run(["cwebp", "-q", "80", "-m", "6", "-metadata", "none",
                        posr, "-o", cel], check=True, capture_output=True)
        print("  dodane: %-18s %6.0f kB" % (nazwa, os.path.getsize(cel) / 1024))


if __name__ == "__main__":
    print("Zmiana nazw:")
    zmien_nazwy()
    print("Nowe zdjecia:")
    doloz()
    suma = sum(os.path.getsize(f) for f in glob.glob(IMG + "/*.webp"))
    print("\nBiblioteka: %d zdjec, %.2f MB"
          % (len(glob.glob(IMG + "/*.webp")), suma / 1048576))
