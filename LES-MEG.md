# Varde – prosjektmappe (GPS Vs Tyv)

Produktnavn: **Varde**. «GPS Vs Tyv» er prosjektnavnet.

Oppdatert 27. oktober 2026. Oppsett på ny PC: se **Varde-oppsett-ny-PC.docx**.

| Fil | Innhold |
|---|---|
| GPS-Vs-Tyv-teknisk-design-v0.13.pdf | Gjeldende tekniske design for Varde, oppdatert etter de elektriske skjemaene, med geofence og produktnavn: konsept, alarmenhet, kamera, CAN-buss, utstyrsbrikker, miljøprofiler og falske alarmer, sensorbuss, brakker og containere, detaljdesign per enhet, plattform, dashboard og app, avarmering, alarmstasjoner, programvare og oppdateringer, marked og hyllevare, komponentliste, kostnadskalkyle og åpne punkter. |
| GPS-Vs-Tyv-elektriske-skjemaer-rev0.1.pdf | Elektriske skjemaer (A3) for hovedenhet (7 ark), kamerapod (2), utvidelsesboks (4), sensornode (1) og utstyrsbrikke S og L (1 hver), med forside, tegnforklaring og stykkliste per kort. Utkast for anbud: pinnenummer og verdier merket * kontrolleres mot datablad. |
| GPS-Vs-Tyv-simulator.html | Interaktiv demo av systemet. Åpnes i nettleser. Dra person, elg og jammer på kartet, eller kjør et av scenarioene. Velg miljø (skog, landlig, by) for alle eller per maskin for å se hvordan falske alarmer unngås. |
| GPS-Vs-Tyv-alarmsentral-prototype.html | Klikkbar prototype av dashboard for bedriften og app for anleggsleder og arbeidere. Åpnes i nettleser. |
| kapslinger/ | 3D-printbare kapslinger v0.1 for alle seks enheter (prototype og felt), STL-filer, bilder og parametrisk kildekode. Se kapslinger/LES-MEG.md. |
| kode/ | Programvare v0.2.1 (token-krav i drift og rettet alarmmodus i fastvaren): plattform med regelmotor, geofence og roller, enkelt dashboard, enhetssimulator og fastvareskjelett for hovedenheten. Referanse for leverandører, se kode/README.md. Kan legges rett i et privat GitHub-repo. |
| kilder/ | Kildefiler for å lage dokumentene på nytt: designdokumentet (HTML → PDF), skjemagenerator (Python → HTML → PDF) og produktvisualiseringen (Claude Design-tavler). Se Word-filen, kapittel 7. |
| Varde-oppsett-ny-PC.docx | Steg for steg: flytte prosjektet, installere programvare, kjøre plattformen lokalt og på Render, 3D-print, lage dokumenter på nytt, feilsøking og lenker til dokumentene på claude.ai. |
| GPS-Vs-Tyv-designgrunnlag-hovedenhet-v1.docx | Første designgrunnlag for hovedenheten (koplingsskjema og kretskort v1). Delvis erstattet av PDF-en, se merknad øverst i dokumentet. |

Merknader:

- Komponentvalg er bare delvis kontrollert mot datablad. Priser, forbruk og innsatsestimater er grove anslag.
- Alle navn, numre og avtaler i prototypene er eksempler.
- HTML-filene henter skrifttyper fra Google Fonts når de er på nett, men fungerer også uten nett.
