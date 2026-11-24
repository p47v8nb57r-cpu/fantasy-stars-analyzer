# Fantasy Stars Analyzer issue checklist

Checked on 24 November 2026 against the local workspace and GitHub `main`. Priorities reflect impact on data freshness, saved cards, and the iPhone experience. Each item states what would make it ready to close.

## P1 · Data freshness and release reliability

- [x] **Publish and verify NHL statistics on GitHub Pages.** The shared NHL workflow explicitly requests a Pages build after pushing new data and fails if the public timestamp remains stale. A push-triggered test on 24 November verified the full automatic path. Scheduled runs use the same steps. [Successful run](https://github.com/p47v8nb57r-cpu/fantasy-stars-analyzer/actions/runs/45502760613) · [NHL workflow](.github/workflows/update-nhl.yml)
- [x] **Reconcile the local checkout with GitHub.** Compared the local files with `main`, kept a copy of the superseded statistics, and moved the local checkout to the published history. The release process now starts from an updated `main`. [Release checks](README.md#release-checks)
- [x] **Keep iPhone confirmation as a release check.** The published portrait release was confirmed on the user’s iPhone. The release process now records both the WebKit check and confirmation on the actual device for future UI changes. [Release checks](README.md#release-checks)

## P2 · Player coverage and saved cards

- [ ] **Keep portrait coverage in sync with the player list.** All 789 players on GitHub `main` currently have a portrait. The separate portrait workflow does not run when only the NHL statistics file changes, so new IDs may be left with initials. Close when new players enter the portrait pipeline automatically, confirmed images are retained on temporary failures, and the workflow reports any IDs still missing a photo. [Portrait workflow](.github/workflows/update-portraits.yml) · [Downloader](scripts/update_portraits.py)
- [ ] **Investigate missing NHL team codes.** The current GitHub season file has 78 skaters without a team code. Some may legitimately be absent from current rosters. Compare missing IDs with NHL records and distinguish roster absence from missing source data. Close when confirmed team changes appear consistently in display and search and unresolved entries still show an explicit unknown status. [Team mapping](scripts/update_nhl.py)
- [ ] **Let users link ambiguous legacy cards to the right NHL player.** Cards and position overrides with a unique name match migrate automatically. Old entries shared by two players with the same name, such as Elias Pettersson, cannot be linked automatically. Close when the user can choose the correct NHL ID from the existing card and the choice survives reload and backup import. [Card linking](index.html)
- [ ] **Make the scope of saved cards clear.** A different site address or browser profile can open with two sample cards, which previously looked like the user's collection was lost. Close when first-run state clearly identifies sample cards and directs users with an existing collection to JSON import. Verify a backup round-trip with cards and position overrides. [Card storage and backup](index.html)

## P3 · Form clarity and maintenance

- [ ] **Expose incomplete form samples.** The statistics script selects five games before checking whether all game stats are available, so a player can have fewer than five usable games. The daily leader requires five complete games. Close when a partial sample is clearly labeled and the leader continues to use five complete games per eligible player. [Form pipeline](scripts/update_nhl.py)
- [ ] **Document season rollover and how to run the app.** The app, updater, and workflow refer to the current season, while the repository README contains only the project title. Close when the README covers local launch, season rollover, statistics and portrait refreshes, and the public app URL. [README](README.md)
