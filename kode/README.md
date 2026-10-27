# Varde – første versjon av programvaren

Produktnavn: Varde. Prosjektnavn: GPS Vs Tyv.

Referanseimplementasjon som grunnlag for leverandører. Den viser at hovedideene virker i praksis. Den er ikke ferdig for drift.

## Oppbygging

Ett plattformprogram med roller, ikke mange programmer. Fastvaren i enhetene er egne programmer.

| Mappe | Språk | Innhold |
|---|---|---|
| shared/ | TypeScript | Meldingsformat (CBOR) og signering (ECDSA P-256), felles for plattform og simulator |
| platform/ | TypeScript | Mottak fra enheter, regelmotor (heartbeat, jamming, sabotasje, miljøprofil, geofence), alarmsaker, eskalering, roller, live-oppdatering, DC-09-formatering |
| dashboard/ | HTML/JavaScript | Enkelt dashboard for mottak og håndtering |
| simulator/ | TypeScript | Virtuelle enheter som snakker samme protokoll som ekte enheter |
| firmware/hovedenhet/ | C (Zephyr) | Fastvareskjelett med alarmlogikk, heartbeat, kanalvalg og meldingskoding |
| test/ | TypeScript | Tester, inkludert kontroll av at fastvaren og plattformen koder meldinger byte for byte likt |

## Kjøre

Krever Node.js 22.18 eller nyere. Ingen pakker må installeres.

    npm run dev            # plattform på http://localhost:8080 i utviklingsmodus
    npm start              # plattform i drift: krever GVT_ADMIN_TOKEN og GVT_OPERATOR_TOKEN
    npm run sim            # i et nytt vindu: interaktiv simulator, skriv "hjelp"
    npm run sim:auto       # fast scenario som kontrollerer alt og avslutter
    npm test               # enhetstester
    npm run test:fw        # fastvaretester på PC (krever gcc eller clang)

Åpne http://localhost:8080 i nettleseren. I utviklingsmodus er token for operatør `operator-dev`, og `admin-dev` brukes for å endre miljøprofil.

**I drift starter ikke plattformen uten token.** Sett `GVT_ADMIN_TOKEN` og `GVT_OPERATOR_TOKEN`, hver minst 32 tegn og ulike, for eksempel laget med `openssl rand -base64 32`. Utviklingsverdiene `admin-dev` og `operator-dev` avvises utenfor utviklingsmodus, og tokenene sammenlignes på konstant tid.

## Geofence

Hvert anlegg kan ha ett eller flere gjerder (mangekant + buffer i meter), lagt inn med `POST /api/geofences` (admin) og listet med `GET /api/geofences`. Enhetene sender posisjon i meldingen (felt 12). Plattformen krever to posisjoner på rad utenfor gjerdet før enheten regnes som ute. Armert (natt) gir alarm med prioritet 1 (kode GF, sendes som BA til alarmstasjon). Avarmert (arbeidstid) gir bare forvarsel. Fastvaren har en egen kopi av gjerdet (`firmware/hovedenhet/src/geofence.c`), slik at enheten merker det selv når mobilnettet er jammet. I simulatoren: `flytt <n> <meter>`, `avarmer <n>` og `armer <n>`.

## Hvor det kan ligge

- **GitHub:** hele mappen, som privat repo. `.github/workflows/test.yml` kjører alle tester ved hver endring.
- **Plattformen:** må kjøre kontinuerlig. Bruk en containertjeneste med minst én instans alltid på, for eksempel Azure Container Apps (Norway East) eller Google Cloud Run, eller en egen server. Se `Dockerfile`. Netlify og Firebase Functions passer ikke, fordi de bare kjører kortvarig når de blir kalt, og da oppdages ikke stillhet.
- **Dashboardet** kan i tillegg ligge på Netlify eller Firebase Hosting når plattformen har eget domene.

## Forenklet i denne versjonen

- Lagring i JSON-fil, ikke PostgreSQL.
- Faste token for admin og operatør, ikke innlogging med Entra ID eller BankID og roller per kunde og anlegg.
- Enhetene sender over HTTP. I drift: CoAP/DTLS eller MQTT over TLS via LTE-M, NTN og LoRa-gateway.
- Varsling skrives til konsollen. Push, SMS og taleanrop koples på av leverandøren.
- DC-09 bare formatering. Kryptering og forbindelse avtales med hver alarmstasjon.
- Ingen app ennå (Flutter eller React Native mot samme API).
- Fastvaren er ikke testet på maskinvare.

Se designdokumentet (PDF) for full arkitektur, sikkerhetskrav og plan.
