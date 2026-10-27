# Varde – 3D-printede kapslinger v0.1

Kapslinger for prototype og felttest av hovedenhet, kamerapod, brikke S og L, sensornode og utvidelsesboks.
Full printinstruksjon står i dokumentet «Varde – 3D-printede kapslinger».

## Innhold

- `stl/` – 26 STL-filer, lagt slik de skal printes. Navn: `varde-<enhet>-<del>-<variant>.stl`
  - `prototype`: PETG, tynnere vegger, uten pakning
  - `felt`: ASA eller SLS PA12, spor for pakningssnor, hull for trykkutjevningsventil
- `bilder/` – forhåndsvisning av feltvarianten
- `kilde/` – parametrisk modell. `python3 varde_kapsling.py` lager alle filene på nytt (bare Python 3, ingen pakker).
  `python3 meshcheck.py stl/*.stl` kontrollerer at filene er lukkede volumer.

## Før print

Kretskortene er ikke tegnet ennå. Hullplassering for kortstolper, radar, reed-bryter og kamera følger designdokumentet
og er merket SJEKK i `varde_kapsling.py`. Juster disse når kortene er klare.

Brikke S blir ca. 19 mm høy, ikke 14 mm som i designdokumentet, fordi ER14250-batteriet er 14,5 mm i diameter.

## Ikke for salg

Kapslingene er ikke sertifisert for IP67, IK10 eller CE. Produksjonskapslingen må konstrueres av leverandøren.
