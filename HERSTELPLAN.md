# Herstelplan energiedashboard — november 2026

## Vastgestelde status (22 november 2026)
- Supabase-project: Energy dashboard (`fapqugkulfxfmisrfeuc`).
- `p1_measurements`: 1.038 records; laatste 22-11-2026 11:49:56 UTC; alleen `location_name = Fleur en Stef`.
- `solar_production`: 27 records; laatste 12-10-2026 11:45 UTC.
- SolarEdge OAuth `expires_at`: 12-10-2026 13:02 UTC, dus verlopen.
- Edge Function `solaredge-production` is actief en bevat refresh-tokenlogica. Oorzaak niet bewezen: controleer scheduling, aanroep en SolarEdge OAuth-respons. Geen tokens of secrets loggen.
- GitHub-repositories bevatten een README; de oorspronkelijke dashboardfrontend is nog niet gelokaliseerd. Niet zonder verificatie vervangen.

## Herstelvolgorde
1. Controleer waar de dashboardwebsite gehost wordt en vind de oorspronkelijke frontend.
2. Controleer of de SolarEdge-functie periodiek wordt aangeroepen; controleer fouten zonder geheimen te tonen.
3. Test tokenvernieuwing via een geauthenticeerde aanroep; bij geweigerd refresh-token opnieuw autoriseren.
4. Controleer of nieuwe SolarEdge-kwartiermetingen worden opgeslagen en of historische lacunes op te vullen zijn.
5. Controleer P1-meetinterval, tijdzone, datakwaliteit, ontbrekende intervallen en het onderscheid tussen de twee huishoudens.
6. Bouw kostenberekening op geverifieerde import/export-kWh, gas-m³ en geldige tariefperioden. Integreer daarna UI.

## Gewenste dashboardonderdelen
- Hoofdscherm: kosten vandaag, maand, jaar; elektriciteit, gas, terugleververgoeding, vaste posten en belastingen.
- Elektriciteit: afname, teruglevering, productie, eigen gebruik, pieken, datavolledigheid.
- Verwarming: ochtend-cv versus airco; testscenario voor voorverwarmen op zonne-overschot, temperatuurmetingen vereist voor opslagduur.
- Tarieven: ENGIE variabel, geldigheidsdatum, importprijs, exportvergoeding, gasprijs, vaste leveringskosten, netbeheer, terugleverkosten en belastingvermindering.
- Vanaf 2027 salderingsregels als aparte versie modelleren; geen 2026-tarieven blind doortrekken.

## Datakwaliteit en berekeningen
- P1 `net_power_w` is vermogen (W), geen kWh. Integreer alleen over aantoonbare tijdsintervallen en markeer gaten; bij lange gaten geen stille extrapolatie.
- Negatief netvermogen = export, positief = import (verifieer P1-conventie).
- SolarEdge `energy_wh` kan een interval- of cumulatieve waarde zijn: eerst API-semantiek controleren voordat productie wordt opgeteld.
- Houd woning en tweede huishouden gescheiden waar meters/databronnen dat toelaten. Tel geen geneste meters dubbel.
- Kosten per periode: som van werkelijk gemeten import-kWh × op dat moment geldig importtarief, minus export-kWh × geldige exportvergoeding, plus gas-m³ × gastarief en toegewezen vaste kosten; belastingen/saldering/terugleverkosten apart modelleren.
- Toon **werkelijk**, **schatting** of **onvolledig** bij iedere KPI.
- Aircoverbruik niet uit totale netafname afleiden zonder afzonderlijke meting of expliciete schatting.

## Veiligheid
- Geen Supabase service_role, SolarEdge OAuth-tokens of setup keys in frontend of repository opslaan.
- RLS behouden; gebruik geauthenticeerde toegang en een veilige serverlaag voor privé-energiegegevens.
