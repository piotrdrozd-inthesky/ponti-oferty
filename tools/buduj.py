#!/usr/bin/env python3
"""Sklada strony PONTI z szablonow i danych.

    python3 tools/buduj.py

Wejscie:  szablony/*.html + data/baza.json + data/asystent.json
Wyjscie:  goscie.html, partnerska.html, voucher.html, index.html w katalogu repo

Zasada: tresci NIE poprawiamy w HTML. Poprawiamy w data/*.json i uruchamiamy
ten skrypt. Inaczej za tydzien nie bedzie wiadomo, ktora wersja jest prawdziwa.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SZAB = os.path.join(REPO, "szablony")
DANE = os.path.join(REPO, "data")


def wczytaj(nazwa):
    with open(os.path.join(DANE, nazwa), encoding="utf-8") as f:
        return json.load(f)


def zl(n):
    """1600 -> '1 600'"""
    return "{:,}".format(n).replace(",", " ")


def wyd_agencyjne(baza):
    """Wydarzenia, ktore agencja/wedding planner moze nam polecic.

    Wyklucza pozycje z kategoria != "wydarzenie" (np. "para" - kolacja i
    Wellness dla dwojga to produkt indywidualny, nie cos, co bierze sie z
    ulotki agencji eventowej. Ta lista karmi chooser, pasy okazji, sekcje
    cenowe i kalkulator prowizji w goscie.html i partnerska.html.
    """
    return [w for w in baza["wydarzenia"] if w.get("kategoria", "wydarzenie") == "wydarzenie"]


MINIMUM_DOTYCZY = ["chrzciny", "komunia", "urodziny", "firmowka", "wigilia", "panienskie", "wesele"]


# ══════════════════════════════════════════════════════════════════
#  Generatory sekcji
# ══════════════════════════════════════════════════════════════════

def gen_chooser(wyd, feature=True):
    """Karty selektora okazji. Wydarzenie z polem "chooser_tlo" (lista 2-3
    nazw plikow z assets/img/) dostaje pelnoszerokosc, zdjecia w tle jako
    auto-slider bez JS i plakietke z tagline - odznacza sie od reszty siatki
    zamiast byc jedna z rownych kart. Zobacz .ch-card--feature w goscie.css.

    `feature=False` wylacza to dla stron bez tego CSS (partnerska.html ma
    wlasny arkusz partnerska.css, ktory nie zna klas .ch-card--feature/
    .ch-slides/.ch-badge - bez tego przelacznika karta kompleksu wyszlaby
    tam bez stylu).
    """
    out = []
    for i, w in enumerate(wyd, 1):
        tlo = w.get("chooser_tlo") if feature else None
        if tlo:
            slajdy = "\n".join(
                '            <img class="ch-slide" src="assets/img/%s.webp" alt="">' % f
                for f in tlo)
            plakietka = ('<span class="ch-badge">%s</span>' % w["tagline"]) if w.get("tagline") else ""
            out.append(
                '        <button class="ch-card ch-card--feature" data-pick="%(id)s">\n'
                '          <div class="ch-slides">\n%(slajdy)s\n          </div>\n'
                '          %(plakietka)s\n'
                '          <span class="ch-n">%(nr)02d</span>\n'
                '          <div class="ch-t">%(label)s</div>\n'
                '          <div class="ch-d">%(haczyk)s</div>\n'
                '        </button>'
                % dict(id=w["id"], slajdy=slajdy, plakietka=plakietka, nr=i,
                       label=w["label"], haczyk=w["haczyk"]))
            continue
        tagline = ('<div class="ch-tag">%s</div>' % w["tagline"]) if w.get("tagline") else ""
        out.append(
            '        <button class="ch-card" data-pick="%s">\n'
            '          <span class="ch-n">%02d</span>\n'
            '          <div class="ch-t">%s</div>\n'
            '          <div class="ch-d">%s</div>\n'
            '          %s\n'
            '        </button>' % (w["id"], i, w["label"], w["haczyk"], tagline))
    return "\n".join(out)


def gen_okazje(wyd):
    out = []
    for i, w in enumerate(wyd):
        flip = " flip" if i % 2 else ""
        lista = "\n".join('          <li>%s</li>' % x for x in w["band_lista"])
        tagline = ('<span class="band-tag">%s</span>' % w["tagline"]) if w.get("tagline") else ""
        out.append(
            '    <div class="band rv%(flip)s" data-ev-band="%(id)s">\n'
            '      <div class="band-i"><img src="assets/img/%(foto)s.webp" '
            'alt="%(label_dl)s w PONTI"><span class="bn">%(nr)02d</span></div>\n'
            '      <div class="band-t">\n'
            '        <h3>%(label_dl)s</h3>%(tagline)s\n'
            '        <p>%(band_p)s</p>\n'
            '        <ul class="bl">\n%(lista)s\n'
            '        </ul>\n'
            '      </div>\n'
            '    </div>'
            % dict(w, flip=flip, lista=lista, tagline=tagline, nr=i + 1))
    return "\n".join(out)


def gen_ceny_okazje(wyd):
    out = []
    for w in wyd:
        # prawa kolumna: co dostajecie
        dost = "\n".join("<li>%s</li>" % x for x in w["dostajecie"])

        if w.get("typowo"):
            typowo = ("<div>Typowy rachunek<b>około %d zł / os.</b></div>"
                      % w["typowo"])
            przyklad = (
                '        <div class="pr-ex">Przykład z życia: '
                '<b>%d osób × około %d zł = %s zł</b> za całość. To pełny rachunek - '
                'z jedzeniem, napojami i obsługą, bez niespodzianek na końcu.</div>\n'
                % (w["przyklad_osob"], w["typowo"],
                   zl(w["przyklad_osob"] * w["typowo"])))
            zaleznosc = ("<li>Napoje i alkohol - to one robią różnicę między %d a %d zł</li>"
                         % (w["od"], w["typowo"]))
        else:
            typowo = ("<div>Typowy rachunek<b>%s</b></div>"
                      % w.get("bez_typowego", "wyceniamy indywidualnie"))
            przyklad = (
                '        <div class="pr-ex">Nie podajemy tu gotowej sumy, bo byłaby '
                'nieprawdziwa. <b>%s</b> - napiszcie, co planujecie, a policzymy '
                'to na konkretach.</div>\n' % w.get("bez_typowego", "Wycena indywidualna"))
            zaleznosc = "<li>Napoje i alkohol - przy wieczornych terminach robią połowę rachunku</li>"

        tagline = ('<span class="pr-tag">%s</span>' % w["tagline"]) if w.get("tagline") else ""

        # niektore wydarzenia (np. kompleks) maja gotowa liste tego, co mozna
        # dolozyc do koszyka - realne pozycje z dodatkow, wypisane wprost przy
        # cenie, zeby gosc zobaczyl je od razu, bez szukania w sekcji Dodatki.
        if w.get("mozna_dolozyc"):
            pozycje = "\n".join(
                '              <div class="pk-line"><span class="pk-name">%s</span>'
                '<span class="pk-dots"></span><span class="pk-price">%s</span></div>'
                % (nazwa, cena) for nazwa, cena in w["mozna_dolozyc"])
            dolozyc = (
                '        <div class="pr-addons">\n'
                '          <h4>Czym powiększycie budżet, jeśli chcecie więcej</h4>\n'
                '%s\n'
                '        </div>\n' % pozycje)
        else:
            dolozyc = ""

        out.append(
            '      <div class="pr-hero rev" data-ev-price="%(id)s">\n'
            '        <div class="pr-top">\n'
            '          <div class="pr-big">\n'
            '            <span class="pr-lab">Menu od</span>\n'
            '            <div class="pr-num">%(od)d zł<small>za osobę</small></div>\n'
            '          </div>\n'
            '          <div class="pr-side">\n'
            '            %(tagline)s\n'
            '            <h3>%(naglowek_ceny)s</h3>\n'
            '            <p>%(dlaczego)s</p>\n'
            '            <div class="pr-meta">\n'
            '              %(typowo)s\n'
            '              <div>Termin<b>%(termin)s</b></div>\n'
            '              <div>Czas trwania<b>%(czas)s</b></div>\n'
            '              <div>Gdzie<b>%(sala)s</b></div>\n'
            '            </div>\n'
            '          </div>\n'
            '        </div>\n'
            '        <div class="pr-cols">\n'
            '          <div><h4>Co dostajecie</h4><ul>%(dost)s</ul></div>\n'
            '          <div><h4>Od czego zależy cena</h4><ul>\n'
            '            <li>Pora dnia - wieczór zawsze kosztuje więcej niż popołudnie</li>\n'
            '            <li>Czas trwania - każda kolejna godzina to obsługa i zablokowana sala</li>\n'
            '            %(zaleznosc)s\n'
            '            <li>Liczba gości wpływa na cenę <em>najmniej</em> ze wszystkiego</li>\n'
            '          </ul></div>\n'
            '        </div>\n'
            '%(przyklad)s'
            '%(dolozyc)s'
            '      </div>'
            % dict(w, dost=dost, typowo=typowo, przyklad=przyklad, zaleznosc=zaleznosc,
                   tagline=tagline, dolozyc=dolozyc))
    return "\n".join(out)


def gen_ceny_progi(progi):
    out = ['    <div class="pr-tiers">']
    for p in progi:
        hot = " hot" if p.get("polecane") else ""
        badge = ('<span class="pr-badge">%s</span>' % p["badge"]) if p.get("badge") else ""
        out.append(
            '        <div class="pr-tier%s rev">%s\n'
            '          <span class="rom">%s</span>\n'
            '          <h4>%s</h4>\n'
            '          <div class="pnum">%d <span>zł / os.</span></div>\n'
            '          <p class="sk">%s</p>\n'
            '          <p class="eq">%s</p>\n'
            '        </div>'
            % (hot, badge, p["nazwa"], p["podtytul"], p["cena"],
               p["zawiera"], p["porownanie"]))
    out.append('    </div>')
    return "\n".join(out)


def gen_ceny_zaufanie():
    """Kolumna "czego nie doliczamy" - bez pozycji o oplacie serwisowej.

    Strona ponti.restaurant podaje w FAQ oplate serwisowa 10% dla grup powyzej
    6 osob. Dopoki to nie jest wyjasnione, oferta nie moze obiecywac jej braku.
    """
    w_cenie = [
        "Obsługa kelnerska przez cały czas trwania wydarzenia",
        "Nakrycie, zastawa, obrusy i świece",
        "Ustawienie sali pod Waszą liczbę gości",
        "Ustalenie menu i degustacja przy większych wydarzeniach",
        "Miejsce na własny tort - bez opłaty za wniesienie",
    ]
    nie = [
        "Opłaty za rezerwację sali",
        "Dopłaty za wniesienie własnego tortu",
        "Dopłaty za dekoracje, które przynosicie sami",
        "Dopłaty za to, że okazja jest uroczysta",
    ]
    return (
        '    <div class="pr-trust rev">\n'
        '      <div class="pr-tbox yes"><h4>W cenie, bez dopłat</h4><ul>%s</ul></div>\n'
        '      <div class="pr-tbox no"><h4>Czego nie doliczamy</h4><ul>%s</ul></div>\n'
        '    </div>'
        % ("".join("<li>%s</li>" % x for x in w_cenie),
           "".join("<li>%s</li>" % x for x in nie)))


def gen_ceny_minimum(mini, poj):
    """Sekcja minimum konsumpcyjnego - widoczna tylko dla okazji, przy ktorych
    wykupienie calej restauracji na wylacznosc ma sens (MINIMUM_DOTYCZY).
    Konferencja i pelny kompleks maja wlasna, indywidualna wycene - pokazanie
    tu gotowej tabeli za wylacznosc myliloby, sugerujac sztywny cennik tam,
    gdzie go celowo nie ma.
    """
    wiersze = "\n".join(
        '        <tr><td class="w">%s</td><td class="k">%s</td>'
        '<td class="l">minimum konsumpcyjne</td></tr>' % (k, v)
        for k, v in mini["pozycje"])
    return (
        '    <div class="pr-min rev" data-ev-minimum="%s">\n'
        '      <div class="pr-min-h">\n'
        '        <h4>%s</h4>\n'
        '        <p>%s Sala Onda mieści do %d osób, cała restauracja z tarasem do %d, '
        'a strefa Wellness do %d.</p>\n'
        '      </div>\n'
        '      <table class="mintab">\n%s\n      </table>\n'
        '      <div class="pr-min-h" style="padding:1.2rem 1.6rem 1.5rem">\n'
        '        <p style="font-size:.86rem;color:var(--mute)">%s</p>\n'
        '      </div>\n'
        '    </div>'
        % (" ".join(MINIMUM_DOTYCZY), mini["naglowek"], mini["opis"], poj["onda"],
           poj["restauracja"], poj["wellness_wylacznosc"], wiersze, mini["rada"]))


def gen_pakiety(dodatki):
    # dwie kolumny: pierwsze dwie grupy w lewej, reszta w prawej
    kolumny = [dodatki[:2], dodatki[2:]]
    out = ['    <div class="pk-cols rv d1">']
    for kol in kolumny:
        out.append('      <div>')
        for g in kol:
            out.append('        <div class="pk-group" data-ev-group="%s">' % g["grupa"])
            out.append('          <h4>%s</h4>' % g["grupa"])
            for p in g["pozycje"]:
                out.append(
                    '          <div class="pk-row" data-ev-pack="%s">\n'
                    '            <div class="pk-line"><span class="pk-name">%s</span>'
                    '<span class="pk-dots"></span><span class="pk-price">%s</span></div>\n'
                    '            <p class="pk-desc">%s</p>\n'
                    '          </div>'
                    % (" ".join(p["ev"]), p["nazwa"], p["cena"], p["opis"]))
            out.append('        </div>')
        out.append('      </div>')
    out.append('    </div>')
    return "\n".join(out)


def gen_fakty(poj):
    f = [
        ("Sala Onda", "do %d osób" % poj["onda"], "Osobna sala na wyłączność"),
        ("Restauracja", "do %d osób" % poj["restauracja"], "Sala, lounge i taras"),
        ("Wellness", "do %d osób" % poj["wellness_wylacznosc"], "Strefa na wyłączność"),
        ("Nocleg", "Na miejscu", "Apartamenty w tym samym budynku"),
        ("Odpowiedź", "24 godziny", "Na każde zapytanie grupowe"),
    ]
    return ('    <div class="facts rv d1">\n%s\n    </div>' % "\n".join(
        '      <div class="fact"><div class="fl">%s</div><div class="fv">%s</div>\n'
        '        <div class="fd">%s</div></div>' % x for x in f))


def gen_sale(sale):
    out = ['    <div class="sale-grid">']
    for s in sale:
        li = "\n".join('        <li>%s</li>' % x for x in s["cechy"])
        out.append(
            '      <div class="sale-c rv">\n'
            '        <div class="ph"><img src="assets/img/%s.webp" alt="%s">'
            '<span class="cap-n">%s</span></div>\n'
            '        <div class="bd">\n'
            '          <h3>%s</h3>\n'
            '          <div class="poj">%s</div>\n'
            '          <p>%s</p>\n'
            '          <ul>\n%s\n          </ul>\n'
            '        </div>\n'
            '      </div>'
            % (s["foto"], s["nazwa"], s["pojemnosc"], s["nazwa"],
               s["pojemnosc"], s["opis"], li))
    out.append('    </div>')
    return "\n".join(out)


def gen_wellness(we):
    karty = []
    for w in we["warianty"]:
        poz = "\n".join(
            '          <div><span>%s</span><span class="dots"></span><b>%s</b></div>'
            % (k, v) for k, v in w["pozycje"])
        karty.append(
            '        <div class="well-c rv">\n'
            '          <h4>%s</h4>\n'
            '          <div class="sub">%s</div>\n'
            '          <p>%s</p>\n'
            '          <div class="well-pr">\n%s\n          </div>\n'
            '          <div class="foot">%s</div>\n'
            '        </div>'
            % (w["nazwa"], w["podtytul"], w["opis"], poz, w["stopka"]))

    zab = "\n".join(
        '        <div><span>%s</span><span class="dots"></span>'
        '<span class="c">%s</span></div>' % (n, c) for n, c in we["zabiegi"])

    return (
        '    <div class="well-head rv">\n'
        '      <div class="mark"><span class="n">06</span><span class="r"></span>'
        '<span class="t">Wellness</span></div>\n'
        '      <h2>%(nazwa)s</h2>\n'
        '      <p>%(opis)s</p>\n'
        '    </div>\n'
        '    <div class="well-grid">\n'
        '      <div class="well-ph rv"><img src="assets/img/jacuzzi-wieczor.webp" '
        'alt="Jacuzzi z widokiem na Odrę"></div>\n'
        '      <div class="well-cards">\n%(karty)s\n      </div>\n'
        '    </div>\n'
        '    <div class="well-zab rv d2">\n'
        '      <h4>Masaże, rytuały i zabiegi w gabinetach obok strefy</h4>\n'
        '      <div class="well-zl">\n%(zab)s\n      </div>\n'
        '      <p class="well-note">%(zrodlo)s</p>\n'
        '      <div class="well-bon">Po kolacji w PONTI dostajecie voucher '
        '%(bon)d zł na strefę Wellness</div>\n'
        '    </div>'
        % dict(nazwa=we["nazwa"], opis=we["opis"], karty="\n".join(karty),
               zab=zab, zrodlo=we["zabiegi_zrodlo"], bon=we["voucher_po_kolacji"]))


# ══════════════════════════════════════════════════════════════════
#  Sekcje tylko dla oferty partnerskiej
# ══════════════════════════════════════════════════════════════════

def gen_tabs(wyd):
    out = []
    for i, w in enumerate(wyd):
        on = " on" if i == 0 else ""
        out.append('      <button class="tab%s" data-t="%s">%s</button>'
                   % (on, w["id"], w["label"]))
    return "\n".join(out)


def gen_panes(wyd):
    out = []
    for i, w in enumerate(wyd):
        on = " on" if i == 0 else ""
        li = "\n".join('            <li>%s</li>' % x for x in w["band_lista"])
        out.append(
            '      <div class="pane%s" data-p="%s">\n'
            '        <div>\n'
            '          <h3>%s</h3>\n'
            '          <p>%s</p>\n'
            '          <ul class="plist">\n%s\n'
            '            <li>%s</li>\n'
            '          </ul>\n'
            '        </div>\n'
            '        <div class="pane-img"><img src="assets/img/%s.webp" alt="%s w PONTI"></div>\n'
            '      </div>'
            % (on, w["id"], w["label_dl"], w["band_p"], li, w["sala"],
               w["foto"], w["label_dl"]))
    return "\n".join(out)


def gen_ceny_okazje_partner(wyd, stawka):
    """To samo co u gosci, plus policzona prowizja partnera pod kazda okazja."""
    out = []
    for w in wyd:
        dost = "\n".join("<li>%s</li>" % x for x in w["dostajecie"])
        if w.get("typowo"):
            typowo = "<div>Typowy rachunek<b>około %d zł / os.</b></div>" % w["typowo"]
            wartosc = w["przyklad_osob"] * w["typowo"]
            prowizja = int(round(wartosc * stawka / 100.0))
            ex = ('        <div class="pr-ex">Przykład: <b>%d osób × %d zł = %s zł</b> '
                  'wartości rezerwacji. Wasza prowizja: <b>%s zł</b> za jedno '
                  'polecenie.</div>\n'
                  % (w["przyklad_osob"], w["typowo"], zl(wartosc), zl(prowizja)))
            zaleznosc = ("<li>Napoje i alkohol - to one robią różnicę między %d a %d zł</li>"
                         % (w["od"], w["typowo"]))
        else:
            typowo = ("<div>Typowy rachunek<b>%s</b></div>"
                      % w.get("bez_typowego", "wyceniamy indywidualnie"))
            ex = ('        <div class="pr-ex">Tu nie podajemy gotowej sumy, bo zależy '
                  'od zakresu. <b>%s</b> - Wasza prowizja to zawsze %d%% pełnej '
                  'wartości rachunku, także od noclegu i strefy Wellness, jeśli '
                  'wejdą w pakiet.</div>\n'
                  % (w.get("bez_typowego", "Wycena indywidualna"), stawka))
            zaleznosc = "<li>Napoje i alkohol - przy wieczornych terminach robią połowę rachunku</li>"

        tagline = ('<span class="pr-tag">%s</span>' % w["tagline"]) if w.get("tagline") else ""
        out.append(
            '      <div class="pr-hero rev" data-ev-price="%(id)s">\n'
            '        <div class="pr-top">\n'
            '          <div class="pr-big">\n'
            '            <span class="pr-lab">Menu od</span>\n'
            '            <div class="pr-num">%(od)d zł<small>za osobę</small></div>\n'
            '          </div>\n'
            '          <div class="pr-side">\n'
            '            %(tagline)s\n'
            '            <h3>%(naglowek_ceny)s</h3>\n'
            '            <p>%(dlaczego)s</p>\n'
            '            <div class="pr-meta">\n'
            '              %(typowo)s\n'
            '              <div>Termin<b>%(termin)s</b></div>\n'
            '              <div>Czas trwania<b>%(czas)s</b></div>\n'
            '              <div>Gdzie<b>%(sala)s</b></div>\n'
            '            </div>\n'
            '          </div>\n'
            '        </div>\n'
            '        <div class="pr-cols">\n'
            '          <div><h4>Co dostaje klient</h4><ul>%(dost)s</ul></div>\n'
            '          <div><h4>Od czego zależy cena</h4><ul>\n'
            '            <li>Pora dnia - wieczór zawsze kosztuje więcej niż popołudnie</li>\n'
            '            <li>Czas trwania - każda kolejna godzina to obsługa i zablokowana sala</li>\n'
            '            %(zaleznosc)s\n'
            '            <li>Liczba gości wpływa na cenę <em>najmniej</em> ze wszystkiego</li>\n'
            '          </ul></div>\n'
            '        </div>\n'
            '%(ex)s'
            '      </div>'
            % dict(w, dost=dost, typowo=typowo, ex=ex, zaleznosc=zaleznosc, tagline=tagline))
    return "\n".join(out)


def gen_pakiety_partner(dodatki):
    """Partnerska ma jedna kolonne grup (.pk-grid), nie dwie."""
    out = ['    <div class="pk-grid">']
    for g in dodatki:
        out.append('      <div class="pk-group rev" data-ev-group="%s">' % g["grupa"])
        out.append('        <h4>%s</h4>' % g["grupa"])
        for p in g["pozycje"]:
            out.append(
                '        <div class="pk-row" data-ev-pack="%s">\n'
                '          <div class="pk-line"><span class="pk-name">%s</span>'
                '<span class="pk-dots"></span><span class="pk-price">%s</span></div>\n'
                '          <p class="pk-desc">%s</p>\n'
                '        </div>'
                % (" ".join(p["ev"]), p["nazwa"], p["cena"], p["opis"]))
        out.append('      </div>')
    out.append('    </div>')
    return "\n".join(out)


def gen_calc_chipy(wyd):
    """Presety kalkulatora prowizji - tylko okazje z policzalnym rachunkiem."""
    out = ['      <div class="chips">']
    pierwszy = True
    for w in wyd:
        if not w.get("typowo"):
            continue
        on = " on" if pierwszy else ""
        pierwszy = False
        out.append('        <button class="chip%s" data-people="%d" data-avg="%d">%s</button>'
                   % (on, w["przyklad_osob"], w["typowo"], w["label"]))
    out.append('      </div>')
    return "\n".join(out)


def gen_wellness_cennik(we):
    """Jawny cennik strefy na landingu voucherow - zeby kwoty na voucherach
    zgadzaly sie z tym, co widzi gosc na ponti.restaurant."""
    kol = []
    for w in we["warianty"]:
        poz = "\n".join(
            '          <div><span>%s</span><span class="dots"></span><b>%s</b></div>'
            % (k, v) for k, v in w["pozycje"])
        kol.append(
            '      <div class="vc-col">\n'
            '        <h4>%s</h4>\n'
            '        <div class="vc-sub">%s</div>\n'
            '        <div class="vc-poz">\n%s\n        </div>\n'
            '        <p class="vc-foot">%s</p>\n'
            '      </div>' % (w["nazwa"], w["podtytul"], poz, w["stopka"]))
    return (
        '    <div class="vc rv">\n'
        '      <div class="vc-head">\n'
        '        <h3>Ile realnie kosztuje strefa Wellness</h3>\n'
        '        <p>Voucher kwotowy najłatwiej dobrać, kiedy widać ceny. To ten sam '
        'cennik, który obowiązuje na miejscu. Po kolacji w PONTI dochodzi jeszcze '
        'voucher %d zł na strefę.</p>\n'
        '      </div>\n'
        '      <div class="vc-grid">\n%s\n      </div>\n'
        '    </div>' % (we["voucher_po_kolacji"], "\n".join(kol)))


def gen_ev_label(wyd):
    return "  var EV_LABEL = %s;" % json.dumps(
        {w["id"]: w["label"] for w in wyd}, ensure_ascii=False)


def gen_ev_cfg(wyd):
    copy = {}
    label = {}
    for w in wyd:
        copy[w["id"]] = {
            "heroH": w["hero_h"], "heroP": w["hero_p"], "title": w["label_dl"],
            "mood": w["nastroj"], "foto": w["foto"], "sala": w["sala"],
        }
        label[w["id"]] = w["label"]
    return ("  var EV_COPY = %s;\n  var EV_LABEL = %s;"
            % (json.dumps(copy, ensure_ascii=False),
               json.dumps(label, ensure_ascii=False)))


# krotkie etykiety przyciskow podpowiedzi. Tekst przycisku jest jednoczesnie
# pytaniem, wiec musi zawierac slowa kluczowe swojej wlasnej intencji.
TEMATY = {
    "cena_ogolna": "Ile to kosztuje",
    "od_czego_cena": "Od czego zależy cena",
    "menu_progi": "Jakie menu grupowe",
    "degustacja": "Degustacja przed terminem",
    "termin": "Sprawdź wolny termin",
    "rezerwacja_stolik": "Rezerwacja stolika",
    "wylacznosc": "Wyłączność i minimum",
    "sala_onda": "Sala Onda",
    "ile_osob": "Ile osób się zmieści",
    "wellness_strefa": "Strefa Wellness i jacuzzi",
    "wellness_voucher": "Vouchery",
    "wellness_zabiegi": "Masaże i zabiegi",
    "nocleg": "Nocleg w apartamencie",
    "kompleks": "Cały kompleks",
    "dzieci": "Menu dla dzieci",
    "pies": "Czy można z psem",
    "tort": "Własny tort",
    "alkohol": "Alkohol i open bar",
    "wino": "Karta win",
    "korkowe": "Własny alkohol",
    "muzyka": "Muzyka i DJ",
    "dekoracje": "Dekoracje i kwiaty",
    "personalizacja": "Drukowane menu",
    "lokalizacja": "Gdzie jesteście",
    "parking": "Parking",
    "kuchnia": "Jaka kuchnia",
    "rzemieslnicy": "Skąd produkty",
    "dieta": "Dieta i alergie",
    "widok_taras": "Taras i widok",
    "wnetrze": "Jak wygląda wnętrze",
    "opinie": "Opinie gości",
    "zaliczka": "Zaliczka i faktura",
    "godziny": "Godziny otwarcia",
    "obsluga": "Jak to przebiega",
    "chrzciny_q": "Chrzciny",
    "komunia_q": "Komunia",
    "urodziny_q": "Urodziny",
    "firmowka_q": "Event firmowy",
    "konferencja_q": "Konferencja i szkolenie",
    "panienskie_q": "Wieczór panieński",
    "wesele_q": "Wesele kameralne",
    "para_q": "Kolacja dla dwojga",
    "kompleks_q": "Grupa z innego miasta",
    "kontakt": "Kontakt do restauracji",
}


def gen_kb(asy, baza, wyd=None):
    """Wiedza asystenta czatu. Bez `wyd` (goscie.html) - zna wszystkie okazje.

    Z `wyd` (strony B2B typu firmowa.html) - odcina intencje _q, tematy
    i wgOkazji dla okazji spoza tej strony. Bez tego asystent na stronie
    tylko dla firm odpowiadalby tresciwie na pytania o chrzciny czy wesele,
    ktorych ta strona w ogole nie oferuje.
    """
    firma = baza["firma"]
    intencje_all = [{
        "id": "powitanie",
        "kw": ["czesc", "hej", "dzien dobry", "witam", "halo", "siema", "dobry wieczor"],
        "a": asy["powitanie_baza"],
        "s": 0,
        "nast": ["cena_ogolna", "ile_osob", "wellness_strefa"],
    }] + asy["intencje"]

    if wyd is None:
        intencje = intencje_all
        tematy = TEMATY
        wg_okazji = asy["wg_okazji"]
        wyd_dla_etykiet = baza["wydarzenia"]
    else:
        dozwolone = {w["id"] for w in wyd}
        wyklucz = {"%s_q" % w["id"] for w in baza["wydarzenia"] if w["id"] not in dozwolone}
        intencje = []
        for i in intencje_all:
            if i["id"] in wyklucz:
                continue
            i2 = dict(i)
            if "nast" in i2:
                i2["nast"] = [n for n in i2["nast"] if n not in wyklucz]
            intencje.append(i2)
        tematy = {k: v for k, v in TEMATY.items() if k not in wyklucz}
        wg_okazji = {k: v for k, v in asy["wg_okazji"].items() if k in dozwolone}
        wyd_dla_etykiet = wyd

    braki = [i["id"] for i in intencje if i["id"] != "powitanie" and i["id"] not in TEMATY]
    if braki:
        sys.exit("Brak etykiety w TEMATY dla intencji: %s" % ", ".join(braki))

    kb = {
        "intencje": intencje,
        "tematy": {k: {"q": v} for k, v in tematy.items()},
        "wgOkazji": wg_okazji,
        "mocne": asy["mocne"],
        "niewiem": asy["niewiem"],
        "powitanie": asy["powitanie_baza"],
        "mail": firma["mail"],
        "tel": firma["telefon"],
        "evLabel": {w["id"]: w["label_dl"] for w in wyd_dla_etykiet},
    }
    return "  var KB = %s;" % json.dumps(kb, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════
#  Skladanie
# ══════════════════════════════════════════════════════════════════

def leniwe_obrazki(html):
    """Dokłada loading/decoding do zdjec, zeby strona wchodzila szybciej.

    Hero jest wyjatkiem - to pierwsze, co gosc widzi, wiec laduje sie od razu.
    """
    def zamien(m):
        tag = m.group(0)
        if "loading=" in tag:
            return tag
        return tag[:-1] + ' loading="lazy" decoding="async">'

    czesci = html.split('<div class="hero-img">')
    if len(czesci) == 2:
        hero_i_reszta = czesci[1].split("</div>", 1)
        hero = hero_i_reszta[0].replace(
            "<img ", '<img fetchpriority="high" decoding="async" ', 1)
        html = (czesci[0] + '<div class="hero-img">' + hero + "</div>"
                + re.sub(r"<img [^>]*>", zamien, hero_i_reszta[1]))
    else:
        html = re.sub(r"<img [^>]*>", zamien, html)
    return html


def zbuduj_goscie(baza, asy):
    szablon = open(os.path.join(SZAB, "goscie.html"), encoding="utf-8").read()
    wyd = wyd_agencyjne(baza)
    poj = baza["pojemnosc"]

    regiony = {
        "CHOOSER": gen_chooser(wyd),
        "OKAZJE": gen_okazje(wyd),
        "CENY_OKAZJE": gen_ceny_okazje(wyd),
        "CENY_PROGI": gen_ceny_progi(baza["menu_progi"]),
        "CENY_ZAUFANIE": gen_ceny_zaufanie(),
        "CENY_MINIMUM": gen_ceny_minimum(baza["minimum"], poj),
        "PAKIETY": gen_pakiety(baza["dodatki"]),
        "FAKTY": gen_fakty(poj),
        "SALE": gen_sale(baza["sale"]),
        "WELLNESS": gen_wellness(baza["wellness"]),
        "EV_CFG": gen_ev_cfg(wyd),
        "KB": gen_kb(asy, baza),
        "TEL": baza["firma"]["telefon"],
        "TEL_HREF": baza["firma"]["telefon_href"],
        "MAIL": baza["firma"]["mail"],
        "POJEMNOSC_KROTKO": "Grupy do %d osób" % poj["restauracja"],
    }
    return zloz(szablon, regiony, "goscie.html")


STRONY_B2B = {
    # Jedna strona dla calej kampanii firmowej - integracja, wigilia, konferencja
    # i pelny kompleks razem. Firma widzi wszystkie swoje opcje na raz, ale nigdy
    # okazje rodzinne (chrzciny, komunia, wesele) - te zostaja tylko w goscie.html.
    "firmowa.html": ["firmowka", "wigilia", "konferencja", "kompleks"],
}


def zbuduj_b2b(baza, asy, ids, nazwa):
    """goscie.html zawezone do okazji z `ids` - oferta pod jeden segment maili.

    Kategoria "b2b" w data/baza.json istnieje tylko po to: takie wydarzenie
    (np. wigilia) nie wchodzi do goscie.html ani partnerska.html, a tu tak.
    """
    szablon = open(os.path.join(SZAB, "goscie.html"), encoding="utf-8").read()
    kolejnosc = {i: n for n, i in enumerate(ids)}
    wyd = sorted([w for w in baza["wydarzenia"] if w["id"] in kolejnosc],
                 key=lambda w: kolejnosc[w["id"]])
    if len(wyd) != len(ids):
        sys.exit("%s: brak wydarzen: %s" % (nazwa,
                 set(ids) - {w["id"] for w in wyd}))
    poj = baza["pojemnosc"]
    regiony = {
        "CHOOSER": gen_chooser(wyd),
        "OKAZJE": gen_okazje(wyd),
        "CENY_OKAZJE": gen_ceny_okazje(wyd),
        "CENY_PROGI": gen_ceny_progi(baza["menu_progi"]),
        "CENY_ZAUFANIE": gen_ceny_zaufanie(),
        "CENY_MINIMUM": gen_ceny_minimum(baza["minimum"], poj),
        "PAKIETY": gen_pakiety(baza["dodatki"]),
        "FAKTY": gen_fakty(poj),
        "SALE": gen_sale(baza["sale"]),
        "WELLNESS": gen_wellness(baza["wellness"]),
        "EV_CFG": gen_ev_cfg(wyd),
        "KB": gen_kb(asy, baza, wyd=wyd),
        "TEL": baza["firma"]["telefon"],
        "TEL_HREF": baza["firma"]["telefon_href"],
        "MAIL": baza["firma"]["mail"],
        "POJEMNOSC_KROTKO": "Grupy do %d osób" % poj["restauracja"],
    }
    return zloz(szablon, regiony, nazwa)


class Kontroler(HTMLParser):
    """Pilnuje, czy znaczniki sie domykaja.

    Wstawianie wygenerowanych blokow w szablon lubi zgubic jedno </div> -
    a wtedy pol strony wjezdza w zly kontener i nikt tego nie widzi
    do momentu, gdy oferta jest u klienta.
    """
    SAMOZAMYKAJACE = {"br", "img", "input", "meta", "link", "hr", "source",
                      "col", "area", "base", "embed", "param", "track", "wbr"}
    PILNUJEMY = {"div", "section", "header", "footer", "nav", "ul", "ol",
                 "table", "tr", "figure", "button", "a"}

    def __init__(self):
        HTMLParser.__init__(self)
        self.stos = []
        self.bledy = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SAMOZAMYKAJACE or tag not in self.PILNUJEMY:
            return
        self.stos.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag not in self.PILNUJEMY:
            return
        if not self.stos:
            self.bledy.append("linia %d: </%s> bez otwarcia"
                              % (self.getpos()[0], tag))
            return
        otwarty, linia = self.stos.pop()
        if otwarty != tag:
            self.bledy.append("linia %d: </%s>, a otwarty byl <%s> z linii %d"
                              % (self.getpos()[0], tag, otwarty, linia))


def sprawdz(html, nazwa):
    k = Kontroler()
    k.feed(html)
    bledy = list(k.bledy)
    for tag, linia in k.stos:
        bledy.append("linia %d: <%s> nigdy sie nie zamyka" % (linia, tag))
    if bledy:
        sys.exit("%s - blad struktury HTML:\n  %s" % (nazwa, "\n  ".join(bledy[:8])))


def zloz(szablon, regiony, nazwa):
    for k, v in regiony.items():
        szablon = szablon.replace("{{%s}}" % k, v)
    puste = re.findall(r"\{\{([A-Z_]+)\}\}", szablon)
    if puste:
        sys.exit("%s: nieuzupelnione znaczniki: %s" % (nazwa, ", ".join(set(puste))))
    html = leniwe_obrazki(szablon)
    sprawdz(html, nazwa)
    return html


def zbuduj_partnerska(baza):
    szablon = open(os.path.join(SZAB, "partnerska.html"), encoding="utf-8").read()
    wyd = wyd_agencyjne(baza)
    poj = baza["pojemnosc"]
    stawka = baza["prowizja"]["stawka"]

    regiony = {
        "CHOOSER": gen_chooser(wyd, feature=False),
        "TABS": gen_tabs(wyd),
        "PANES": gen_panes(wyd),
        "CENY_OKAZJE": gen_ceny_okazje_partner(wyd, stawka),
        "CENY_PROGI": gen_ceny_progi(baza["menu_progi"]),
        "CENY_ZAUFANIE": gen_ceny_zaufanie(),
        "CENY_MINIMUM": gen_ceny_minimum(baza["minimum"], poj),
        "PAKIETY": gen_pakiety_partner(baza["dodatki"]),
        "CALC_CHIPY": gen_calc_chipy(wyd),
        "EV_CFG": gen_ev_label(wyd),
        "POJ_MAX": str(poj["restauracja"]),
        "TEL": baza["firma"]["telefon"],
        "TEL_HREF": baza["firma"]["telefon_href"],
        "MAIL": baza["firma"]["mail"],
    }
    return zloz(szablon, regiony, "partnerska.html")


def zbuduj_voucher(baza):
    szablon = open(os.path.join(SZAB, "voucher.html"), encoding="utf-8").read()
    regiony = {
        "WELLNESS_CENNIK": gen_wellness_cennik(baza["wellness"]),
        "TEL": baza["firma"]["telefon"],
        "TEL_HREF": baza["firma"]["telefon_href"],
        "MAIL": baza["firma"]["mail"],
    }
    return zloz(szablon, regiony, "voucher.html")


def main():
    baza = wczytaj("baza.json")
    asy = wczytaj("asystent.json")

    strony = {
        "goscie.html": zbuduj_goscie(baza, asy),
        "partnerska.html": zbuduj_partnerska(baza),
        "voucher.html": zbuduj_voucher(baza),
    }
    for nazwa, ids in STRONY_B2B.items():
        strony[nazwa] = zbuduj_b2b(baza, asy, ids, nazwa)

    for nazwa, tresc in strony.items():
        sciezka = os.path.join(REPO, nazwa)
        open(sciezka, "w", encoding="utf-8").write(tresc)
        print("%-18s %6.1f kB" % (nazwa, os.path.getsize(sciezka) / 1024))
    print("\n%d typow wydarzen, %d intencji asystenta, telefon %s"
          % (len(baza["wydarzenia"]), len(asy["intencje"]) + 1,
             baza["firma"]["telefon"]))


if __name__ == "__main__":
    main()
