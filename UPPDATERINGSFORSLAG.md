# Uppdateringsförslag för Fantasy Stars Analyzer 4.0

Förslagen prioriterar trygg hantering av kortsamlingen på iPhone och bättre stöd inför nästa NHL-omgång. Den tidigare åtgärdslistan finns i [ISSUES.md](ISSUES.md).

## P1 Skydda kortsamlingen

- [x] **Förhandsgranska och slå ihop säkerhetskopior.** Visa antal kort i appen och i backupfilen före import. Låt användaren välja mellan att slå ihop och att ersätta samlingen. Matcha i första hand på NHL-ID och visa skillnader i kortpoäng eller manuella positioner innan någon uppgift skrivs över. Ett testfall är att importera 27 kort till en installation som redan har sex och kunna behålla de kort som bara finns där.
- [x] **Gör det lättare att kontrollera och flytta sin samling.** Visa hur många egna kort som finns i den aktuella installationen under **Mer**, tillsammans med när den senaste säkerhetskopian exporterades. Samla export, import och en kort instruktion för flytt mellan två hemskärmsikoner på samma ställe.

## P2 Förbättra Lagbygge

- [x] **Gör det tydligt vilken omgång som föreslås.** Visa antal matcher per omgång, första matchstart i svensk tid och när schemat uppdaterades. Visa vilka matcher som redan har startat om den valda omgången är i gång.
- [x] **Visa hur varje prognos räknas fram.** Visa säsongssnitt, formsnitt, antal kompletta matcher och motståndarjustering bredvid den beräknade poängen. Användaren ska kunna se varför en spelare rankas högre än en annan.
- [x] **Visa ersättare per position.** Låt användaren se de tre högst rankade tillgängliga ersättarna för en plats. När en spelare byts ut ska laget behålla rätt positioner, räkna om totalprognosen och undvika dubbletter.
- [x] **Spara en uppställning för en omgång.** Låt användaren spara ett förslag och öppna det igen med samma spelare. Visa en markering om någon spelare senare saknar en kommande match eller om prognosen har ändrats sedan laget sparades.

## P3 Underlätta scouting

- [x] **Jämför spelare sida vid sida.** Jämför två eller tre spelare från Scout på samma träningsnivå. Visa säsongssnitt, senaste form, Fantasy Stars-position och nästa motståndare där uppgifterna finns.
- [x] **Följ spelare i en bevakningslista.** Stjärnmärk spelare direkt i Scout och sortera bevakningslistan efter formlyft eller nästa match. Spara listan tillsammans med kort och positioner i JSON-säkerhetskopian.

## Genomförda uppdateringar

1. [x] **Visa utfallet för sparade lag.** Jämför den sparade prognosen med faktiskt utfall efter omgången. Visa skillnaden för varje spelare, lagkortet och hela uppställningen.
2. [x] **Lås val i Lagbygge.** Behåll valda spelare eller lagkort och räkna om de övriga platserna. Kontrollera Fantasy Stars-positioner och uteslut dubbletter.
3. [x] **Visa spelstatus inför match.** Markera bekräftad frånvaro och osäker spelstatus när det finns en verifierad källa. Visa statusen i Lagbygge så att en ersättare kan väljas inför matchstart.
4. [x] **Visa tre kommande matcher i Bevakning.** Visa motståndare och matchtid för varje bevakad spelare, så att spelare med liknande form kan jämföras över flera omgångar.
5. [x] **Ta med sparade lag i JSON-säkerhetskopian.** Exportera och återställ sparade uppställningar tillsammans med kort, manuella positioner och bevakning. Förhandsgranska vilka sparade lag som påverkas vid import.

## Genomförda förbättringar av Lagbygge och Mina kort

1. [x] **Se vilka sparade kort du kan spela i nästa omgång.** Lägg till filtret **Spelar i nästa omgång** under **Mina kort**. Visa motståndare, matchstart och spelstatus när det finns en NHL-rapport. Infört i **4.1.9**.
2. [x] **Bygg ett lag med bara dina ägda kort.** Lägg till ett val i **Lagbygge** mellan **Alla spelare** och **Mina ägda kort**, så att du kan jämföra förslagen. Infört i **4.1.10**.
3. [x] **Jämför flera lagförslag för samma omgång.** Låt användaren spara ett reservförslag bredvid huvudlaget. Visa vilka spelare som skiljer sig och hur mycket totalprognosen ändras. Infört i **4.2.1**.
4. [x] **Se prognosens träffsäkerhet över tid.** Samla färdigspelade omgångar i en historik och visa vilka spelare eller lagkort som oftast hamnar över eller under prognosen. Infört i **4.2.2**.
5. [x] **Få en påminnelse före första nedsläpp.** Visa en notis i **Lagbygge** när första matchstart närmar sig och ett sparat val har osäker spelstatus eller bekräftad frånvaro. Infört i appen i **4.2.3**.

## Nästa tio uppdateringsförslag

1. [ ] **Omgångsplaneraren (kandidat för 5.0).** Föreslå uppställningar för tre kommande omgångar utifrån ägda kort, Fantasy Stars-positioner, motstånd, form och spelstatus. Låt användaren låsa val och jämföra **Maxa nästa omgång** med **Maxa totalen över tre omgångar**. Be om uttryckligt godkännande före ett släpp som 5.0.0.
2. [x] **Samla ändrad spelstatus i Scout.** Lägg till **Statusändringar** med filter för ägda och bevakade spelare. Visa beskedets publiceringstid och om det gäller skada, osäker spelstatus eller möjlig comeback. Infört i **4.3.0**.
3. [ ] **Ge form mindre vikt efter comeback.** Väg in säsongssnittet mer efter längre frånvaro och visa hur många matcher spelaren har spelat sedan återkomsten.
4. [x] **Jämför två spelare för samma lagplats.** Öppna jämförelsen från **Ersättare** i Lagbygge och visa prognos, motstånd, spelstatus och matchstart. Infört i **4.3.2**.
5. [x] **Visa luckor i kortsamlingen.** Visa hur många tillgängliga ägda kort som finns per position för var och en av de tre kommande omgångarna. Infört i **4.3.3**.
6. [ ] **Sortera Scout efter kommande matchprogram.** Visa antalet kommande matcher och hur motståndarna rankas defensivt. Behåll form som ett eget mått.
7. [ ] **Jämför lagkort sida vid sida.** Visa upp till tre lagkort med nästa motståndare och prognosens delar, till exempel räddningar, insläppta mål och vinstchans.
8. [ ] **Följ dina spelares faktiska FPTS efter omgången.** Visa vilka kort i samlingen som gav högst utfall och jämför det sparade huvudlagets utfall med reservförslagets.
9. [ ] **Visa när uppgifterna senast kontrollerades.** Ge schema, statistik och spelstatus egna tidsstämplar under **Mer**. Visa i Lagbygge hur många matcher i omgången som har en inläst NHL-rapport.
10. [ ] **Matchnotiser på iPhone.** När arbetet med pushnotiser återupptas, låt användaren välja att få ett besked om en spelare i det sparade huvudlaget blir osäker eller bekräftat borta nära nedsläpp.

Föreslagen startordning är **2, 4 och 5**. De förbättrar arbetet inför nästa omgång och kan återanvändas i Omgångsplaneraren.
