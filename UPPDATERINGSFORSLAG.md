# Uppdateringsförslag för Fantasy Stars Analyzer 4.0

Förslagen prioriterar trygg hantering av kortsamlingen på iPhone och bättre stöd inför nästa NHL-omgång. Den tidigare åtgärdslistan finns i [ISSUES.md](ISSUES.md).

## P1 Skydda kortsamlingen

- [x] **Förhandsgranska och slå ihop säkerhetskopior.** Visa antal kort i appen och i backupfilen före import. Låt användaren välja mellan att slå ihop och att ersätta samlingen. Matcha i första hand på NHL-ID och visa skillnader i kortpoäng eller manuella positioner innan någon uppgift skrivs över. Ett testfall är att importera 27 kort till en installation som redan har sex och kunna behålla de kort som bara finns där.
- [x] **Gör det lättare att kontrollera och flytta sin samling.** Visa hur många egna kort som finns i den aktuella installationen under **Mer**, tillsammans med när den senaste säkerhetskopian exporterades. Samla export, import och en kort instruktion för flytt mellan två hemskärmsikoner på samma ställe.

## P2 Förbättra Lagbygge

- [ ] **Gör det tydligt vilken omgång som föreslås.** Visa antal matcher per omgång, första matchstart i svensk tid och när schemat uppdaterades. Visa vilka matcher som redan har startat om den valda omgången är i gång.
- [ ] **Visa hur varje prognos räknas fram.** Visa säsongssnitt, formsnitt, antal kompletta matcher och motståndarjustering bredvid den beräknade poängen. Användaren ska kunna se varför en spelare rankas högre än en annan.
- [ ] **Visa ersättare per position.** Låt användaren se de tre högst rankade tillgängliga ersättarna för en plats. När en spelare byts ut ska laget behålla rätt positioner, räkna om totalprognosen och undvika dubbletter.
- [ ] **Spara en uppställning för en omgång.** Låt användaren spara ett förslag och öppna det igen med samma spelare. Visa en markering om någon spelare senare saknar en kommande match eller om prognosen har ändrats sedan laget sparades.

## P3 Underlätta scouting

- [ ] **Jämför spelare sida vid sida.** Jämför två eller tre spelare från Scout på samma träningsnivå. Visa säsongssnitt, senaste form, Fantasy Stars-position och nästa motståndare där uppgifterna finns.
- [ ] **Följ spelare i en bevakningslista.** Stjärnmärk spelare direkt i Scout och sortera bevakningslistan efter formlyft eller nästa match. Spara listan tillsammans med kort och positioner i JSON-säkerhetskopian.
