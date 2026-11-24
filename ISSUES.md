# Fantasy Stars Analyzer issue checklist

Checked on 24 November 2026 against the local workspace and GitHub `main`. Priorities reflect impact on data freshness, saved cards, and the iPhone experience. Each item states what would make it ready to close.

## P1 · Data freshness and release reliability

- [x] **Publish and verify NHL statistics on GitHub Pages.** The shared NHL workflow explicitly requests a Pages build after pushing new data and fails if the public timestamp remains stale. A push-triggered test on 24 November verified the full automatic path. Scheduled runs use the same steps. [Successful run](https://github.com/p47v8nb57r-cpu/fantasy-stars-analyzer/actions/runs/45502760613) · [NHL workflow](.github/workflows/update-nhl.yml)
- [x] **Reconcile the local checkout with GitHub.** Compared the local files with `main`, kept a copy of the superseded statistics, and moved the local checkout to the published history. The release process now starts from an updated `main`. [Release checks](README.md#release-checks)
- [x] **Keep iPhone confirmation as a release check.** The published portrait release was confirmed on the user’s iPhone. The release process now records both the WebKit check and confirmation on the actual device for future UI changes. [Release checks](README.md#release-checks)

## P2 · Player coverage and saved cards

- [x] **Keep portrait coverage in sync with the player list.** The NHL workflow refreshes the portrait manifest with statistics, retains existing images on temporary download failures, and reports IDs still missing a photo. Tested with a simulated new player and a failed download. [NHL workflow](.github/workflows/update-nhl.yml) · [Downloader](scripts/update_portraits.py)
- [x] **Distinguish roster absence from an unknown team.** After validating the NHL roster snapshot, the updater records whether each skater appeared in the current NHL rosters. The UI labels confirmed roster absence separately from older data with unknown status. An absent skater may be in the AHL, but roster absence alone cannot establish that assignment. [Team mapping](scripts/update_nhl.py)
- [x] **Let users link ambiguous legacy cards to the right NHL player.** Cards with more than one NHL name match can be linked in the card editor using position, team and NHL ID. Verified the two Elias Pettersson options, position migration and backup round-trip. [Card linking](index.html)
- [x] **Make the scope of saved cards clear.** Sample cards are labeled and excluded from backups. A collection without saved cards links directly to the JSON import. Verified import with a separate WebKit profile. [Card storage and backup](index.html)

The P2 interface passed WebKit tests at iPhone width. Confirmation on the physical iPhone is tracked separately under the [release checks](README.md#release-checks).

## P3 · Form clarity and maintenance

- [ ] **Expose incomplete form samples.** The statistics script selects five games before checking whether all game stats are available, so a player can have fewer than five usable games. The daily leader requires five complete games. Close when a partial sample is clearly labeled and the leader continues to use five complete games per eligible player. [Form pipeline](scripts/update_nhl.py)
- [ ] **Document season rollover and how to run the app.** The app, updater, and workflow refer to the current season, while the repository README contains only the project title. Close when the README covers local launch, season rollover, statistics and portrait refreshes, and the public app URL. [README](README.md)
