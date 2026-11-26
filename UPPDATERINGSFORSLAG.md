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

## Nästa fem uppdateringar

1. [x] **Visa utfallet för sparade lag.** Jämför den sparade prognosen med faktiskt utfall efter omgången. Visa skillnaden för varje spelare, lagkortet och hela uppställningen.
2. [x] **Lås val i Lagbygge.** Behåll valda spelare eller lagkort och räkna om de övriga platserna. Kontrollera Fantasy Stars-positioner och uteslut dubbletter.
3. [ ] **Visa spelstatus inför match.** Markera bekräftad frånvaro och osäker spelstatus när det finns en verifierad källa. Visa statusen i Lagbygge så att en ersättare kan väljas inför matchstart.
4. [ ] **Visa tre kommande matcher i Bevakning.** Visa motståndare och matchtid för varje bevakad spelare, så att spelare med liknande form kan jämföras över flera omgångar.
5. [ ] **Ta med sparade lag i JSON-säkerhetskopian.** Exportera och återställ sparade uppställningar tillsammans med kort, manuella positioner och bevakning. Förhandsgranska vilka sparade lag som påverkas vid import.
