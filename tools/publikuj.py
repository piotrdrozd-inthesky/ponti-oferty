#!/usr/bin/env python3
"""Sklada folder docs/ pod GitHub Pages.

    python3 tools/publikuj.py

GitHub Pages serwuje publicznie wszystko, co wrzucisz - dlatego:

  * oferta partnerska ma w nazwie pliku losowy dopisek. Klient koncowy nie
    trafi na nia, wpisujac /partnerska.html. Dopisek jest zapisany
    w data/publikacja.json, wiec link nie zmienia sie przy kazdej przebudowie.
  * kazda strona dostaje <meta name="robots" content="noindex,nofollow">
    i dochodzi robots.txt, zeby oferty nie wchodzily do Google.
  * index.html to spis linkow dla Ciebie, nie dla klientow. Nigdzie nie jest
    podlinkowany, ale i tak nie wysylaj go dalej.
"""
import json
import os
import re
import secrets
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")
KONF = os.path.join(REPO, "data", "publikacja.json")

NOINDEX = ('<meta name="robots" content="noindex,nofollow">\n'
           '<meta name="referrer" content="no-referrer">')


def konfiguracja():
    if os.path.exists(KONF):
        k = json.load(open(KONF, encoding="utf-8"))
    else:
        k = {}
    zmieniono = False
    if "partnerska" not in k:
        k["partnerska"] = "wspolpraca-" + secrets.token_hex(4) + ".html"
        zmieniono = True
    if "_o_pliku" not in k:
        k["_o_pliku"] = ("Nazwy plikow na GitHub Pages. Dopisek przy ofercie partnerskiej "
                        "jest losowy, zeby klient koncowy nie trafil na nia przypadkiem. "
                        "Nie zmieniaj go po wyslaniu linkow partnerom. Pole 'domena' to "
                        "wlasna domena spod ktorej dziala GitHub Pages (docs/CNAME) - "
                        "puste jeśli uzywasz domyslnego adresu *.github.io.")
        zmieniono = True
    if "domena" not in k:
        k["domena"] = ""
        zmieniono = True
    if zmieniono:
        json.dump(k, open(KONF, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return k


def wstaw_noindex(html):
    if "noindex" in html:
        return html
    return html.replace('<meta name="viewport"',
                        NOINDEX + '\n<meta name="viewport"', 1)


def main():
    k = konfiguracja()
    baza = json.load(open(os.path.join(REPO, "data", "baza.json"), encoding="utf-8"))
    firma = baza["firma"]

    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(DOCS)

    strony = {
        "goscie.html": "goscie.html",
        "partnerska.html": k["partnerska"],
        "voucher.html": "voucher.html",
        # strony B2B pod kampanie mailowa - kazdy segment widzi tylko swoja
        # okazje, bez chrzcin i komunii (patrz STRONY_B2B w tools/buduj.py)
        "firmowa.html": "firmowa.html",
        "wigilia.html": "wigilia.html",
        "zespol.html": "zespol.html",
    }
    for zrodlo, cel in strony.items():
        html = open(os.path.join(REPO, zrodlo), encoding="utf-8").read()
        open(os.path.join(DOCS, cel), "w", encoding="utf-8").write(wstaw_noindex(html))

    shutil.copytree(os.path.join(REPO, "assets"), os.path.join(DOCS, "assets"),
                    ignore=shutil.ignore_patterns(".DS_Store", "*.jpeg", "*.jpg"))

    if k.get("domena"):
        open(os.path.join(DOCS, "CNAME"), "w", encoding="utf-8").write(k["domena"] + "\n")

    # Pages nie przepuszcza katalogow z podkreslnikiem bez tego pliku
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    open(os.path.join(DOCS, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nDisallow: /\n")

    hub = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
%(noindex)s
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PONTI - linki do ofert (wewnetrzne)</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Poppins:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{--paper:#FBF8F2;--ink:#1F2318;--ink2:#4A4F3E;--terra:#B85C38;--line:rgba(31,35,24,.14);--forest:#1B2113}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Poppins',sans-serif;background:var(--paper);color:var(--ink);
  font-weight:300;line-height:1.75}
.w{max-width:760px;margin:0 auto;padding:0 clamp(1.2rem,5vw,2rem)}
.hero{position:relative;min-height:clamp(220px,32vw,340px);display:flex;align-items:flex-end;
  background:linear-gradient(180deg,rgba(27,33,19,.25),rgba(27,33,19,.82)),
  url('assets/img/dlugi-stol.webp') center 38%%/cover no-repeat;margin-bottom:clamp(2rem,5vw,3rem)}
.hero-in{max-width:760px;margin:0 auto;padding:clamp(2rem,6vw,3rem) clamp(1.2rem,5vw,2rem)
  clamp(1.6rem,4vw,2.2rem);width:100%%;box-sizing:border-box}
h1{font-family:'Instrument Serif',serif;font-weight:400;font-size:clamp(2rem,5vw,3rem);
  line-height:1.1;margin-bottom:.7rem;color:#fff}
.kick{font-size:.62rem;letter-spacing:.3em;text-transform:uppercase;color:#D98A63;
  margin-bottom:1.1rem}
main{padding-bottom:clamp(2rem,7vw,5rem)}
.lead{color:var(--ink2);font-size:.95rem;margin-bottom:2.6rem;max-width:60ch}
.row{display:block;border:1px solid var(--line);padding:1.3rem 1.4rem;margin-bottom:.9rem;
  text-decoration:none;color:inherit;transition:.3s}
.row:hover{border-color:var(--terra);transform:translateY(-2px)}
.row h2{font-family:'Instrument Serif',serif;font-weight:400;font-size:1.5rem;line-height:1.2}
.row .kto{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--terra);
  margin-bottom:.45rem}
.row p{font-size:.85rem;color:var(--ink2);margin-top:.4rem}
.row code{font-family:ui-monospace,monospace;font-size:.76rem;color:#8A8B79;
  word-break:break-all;display:block;margin-top:.55rem}
.uwaga{border-left:2px solid var(--terra);padding:.9rem 1.1rem;background:#F3ECE0;
  font-size:.85rem;color:var(--ink2);margin:2.2rem 0 1rem}
footer{padding-top:1.4rem;border-top:1px solid var(--line);
  font-size:.78rem;color:#8A8B79}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-in">
    <div class="kick">Do uzytku wewnetrznego</div>
    <h1>Linki do ofert PONTI</h1>
  </div>
</div>

<main class="w">
  <p class="lead">Trzy strony, trzy rozne odbiorcy - dlatego stoja osobno, a nie
    na jednej wspolnej. Zanim wyslesz link, sprawdz, do kogo piszesz.</p>

  <a class="row" href="%(partner)s">
    <div class="kto">Tylko dla agencji eventowych i wedding plannerow</div>
    <h2>Oferta partnerska - 10%% prowizji</h2>
    <p>Osiem typow wydarzen, ktore agencja moze nam polecic - od chrzcin po
      pelny kompleks z noclegiem (ALL DAY IN PONTI) - plus przelicznik prowizji
      i zasady wspolpracy. <b>Nigdy nie wysylaj tego linku klientowi koncowemu.</b></p>
    <code>%(partner)s</code>
  </a>

  <a class="row" href="goscie.html">
    <div class="kto">Do przeslania dalej - agencja wysyla to swojemu klientowi</div>
    <h2>Prezentacja wydarzen</h2>
    <p>To samo osiem typow wydarzen, ceny, dodatki, sale, strefa Wellness i asystent
      czatu - ale bez slowa o prowizji. Ten link agencja przekazuje swojemu klientowi
      albo Ty wysylasz go bezposrednio osobie pytajacej o termin.</p>
    <code>goscie.html</code>
  </a>

  <a class="row" href="voucher.html">
    <div class="kto">Publicznie - social media, newsletter</div>
    <h2>Landing voucherow</h2>
    <p>Produkty indywidualne, nie wydarzenia grupowe: vouchery kwotowe i pakietowe,
      kolacja i Wellness dla dwojga, cennik strefy Wellness.</p>
    <code>voucher.html</code>
  </a>

  <a class="row" href="firmowa.html">
    <div class="kto">Kampania B2B - maile o integracjach (firmy 20+)</div>
    <h2>Oferta firmowa</h2>
    <p>Kolacja firmowa, konferencja i pelny kompleks - bez okazji rodzinnych.
      Ten link idzie w mailach o jesiennych integracjach.</p>
    <code>firmowa.html</code>
  </a>

  <a class="row" href="wigilia.html">
    <div class="kto">Kampania B2B - maile wigilijne</div>
    <h2>Wigilia firmowa</h2>
    <p>Tylko wigilia: swiateczne menu, terminy 3-19 grudnia, zasada "nie doliczamy
      niczego za to, ze okazja jest swiateczna".</p>
    <code>wigilia.html</code>
  </a>

  <a class="row" href="zespol.html">
    <div class="kto">Kampania B2B - male zespoly (do 20 osob)</div>
    <h2>Kolacja zespolowa</h2>
    <p>Sama kolacja firmowa w kameralnej skali - sala Onda na wylacznosc
      od kilkunastu osob.</p>
    <code>zespol.html</code>
  </a>

  <div class="uwaga">
    GitHub Pages jest publiczny. Kazda z tych stron ma ustawione noindex, a nazwa
    pliku oferty partnerskiej zawiera losowy dopisek - dlatego nikt na nia nie
    trafi z Google ani z adresu na chybil trafil. Ale kazdy, kto ma link, wejdzie.
  </div>

  <footer>%(nazwa)s &middot; %(adres)s &middot; %(tel)s &middot; %(mail)s</footer>
</main>
</body>
</html>
""" % dict(noindex=NOINDEX, partner=k["partnerska"], nazwa=firma["nazwa"],
           adres=firma["adres_krotki"], tel=firma["telefon"], mail=firma["mail"])

    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(hub)

    waga = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(DOCS) for f in fs)
    print("docs/ gotowe - %.2f MB" % (waga / 1048576))
    for nazwa in sorted(os.listdir(DOCS)):
        p = os.path.join(DOCS, nazwa)
        if os.path.isfile(p):
            print("  %-32s %6.1f kB" % (nazwa, os.path.getsize(p) / 1024))
    print("  assets/                          %6.1f kB"
          % (sum(os.path.getsize(os.path.join(r, f))
                 for r, _, fs in os.walk(os.path.join(DOCS, "assets"))
                 for f in fs) / 1024))
    print("\nLink partnerski: %s" % k["partnerska"])


if __name__ == "__main__":
    main()
