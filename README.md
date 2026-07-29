# Oferty PONTI

Trzy strony sprzedażowe PONTI Restaurant, składane ze wspólnej bazy danych.

Wcześniej były to trzy pliki HTML po 2-5 MB, ze zdjęciami zapisanymi w kodzie.
Działały po dwukliku, ale nie dawały się wysłać linkiem: Dysk Google nie serwuje
HTML jako strony, więc odbiorca dostawał pobieranie pliku, nie ofertę.

Teraz zdjęcia leżą osobno jako WebP, a strony mają po 13-112 kB. Wchodzą przez
link, na telefonie, bez pobierania, i zachowują wszystkie funkcje: wybór typu
wydarzenia, filtrowanie cen i dodatków, przelicznik prowizji, asystenta czatu.

## Co jest czym

| Plik | Dla kogo | Prowizja? |
|---|---|---|
| `goscie.html` | klienci końcowi, goście | nie |
| `partnerska.html` | agencje eventowe, wedding plannerzy | **tak, 10%** |
| `voucher.html` | publicznie, media społecznościowe | nie |

> Nigdy nie wysyłaj oferty partnerskiej klientowi końcowemu. Widzi wtedy,
> że płacimy pośrednikowi 10%, i odczyta to jako narzut na swoim rachunku.

## Jak to zmieniać

**Nie edytuj plików HTML w katalogu głównym - są generowane i zostaną nadpisane.**

```bash
python3 tools/buduj.py
```

Treść i liczby siedzą w `data/`:

| Plik | Co w nim jest |
|---|---|
| `data/baza.json` | dane firmy, pojemności, cennik menu i dodatków, 9 typów wydarzeń, strefa Wellness, minimum konsumpcyjne |
| `data/asystent.json` | wiedza asystenta czatu: 45 tematów, słowa kluczowe, odpowiedzi |
| `data/publikacja.json` | nazwa pliku oferty partnerskiej na GitHub Pages |

Struktura stron jest w `szablony/`, styl w `assets/`. Wygląd wspólny dla
wszystkich trzech stron - responsywność, kolory okazji, pasek akcji na telefonie -
jest w `assets/lift.css`.

## Narzędzia

```bash
python3 tools/buduj.py           # składa trzy strony z danych
python3 tools/test_asystent.py   # sprawdza, czy asystent trafia w tematy
python3 tools/publikuj.py        # przygotowuje docs/ pod GitHub Pages
```

`tools/wyodrebnij_zdjecia.py` i `tools/zrob_szablony.py` to konwersja
jednorazowa ze starych plików z Dysku. Normalnie ich nie uruchamiasz.

## Publikacja

```bash
python3 tools/publikuj.py
git add -A && git commit -m "aktualizacja ofert"
git push
```

W ustawieniach repozytorium: **Settings → Pages → Source: Deploy from a branch,
Branch: main, folder: /docs**.

GitHub Pages jest publiczny, dlatego:

- każda strona ma `noindex, nofollow`, a w `docs/robots.txt` stoi `Disallow: /` -
  oferty nie wejdą do Google,
- oferta partnerska ma w nazwie pliku losowy dopisek, żeby klient nie trafił na
  nią, wpisując `/partnerska.html`. Dopisek jest zapisany w `data/publikacja.json` -
  **nie zmieniaj go po rozesłaniu linków partnerom**, bo stare linki przestaną działać,
- `docs/index.html` to spis linków do użytku wewnętrznego. Nie jest nigdzie
  podlinkowany, ale też go nie rozsyłaj.

Kto ma link, ten wejdzie - to nie jest strona chroniona hasłem.

## Asystent czatu

Siedzi w `goscie.html`, w prawym dolnym rogu. Odpowiada wyłącznie z
`data/asystent.json` i przy pytaniu poza bazą mówi wprost, że nie wie.

Po czterech punktach sygnału zakupowego pokazuje formularz. Domyślnie otwiera
klienta pocztowego gościa. Żeby zapytania szły automatycznie w tle, wpisz adres
formularza (np. z formspree.io) w `szablony/goscie.html`:

```js
var FORM_ENDPOINT = '';
```

i przebuduj strony.

## Zdjęcia

19 zdjęć w `assets/img/`, WebP, maks. 1800 px, razem 3 MB. Wszystkie to własne
zdjęcia PONTI - bez stocków i bez grafik generowanych.

Nowe zdjęcie: wrzuć plik do `assets/img/` jako WebP i wpisz jego nazwę
(bez rozszerzenia) w odpowiednim polu `foto` w `data/baza.json`.
