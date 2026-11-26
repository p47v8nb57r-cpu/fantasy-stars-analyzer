# Fantasy Stars Analyzer

The public app runs at [Fantasy Stars Analyzer](https://p47v8nb57r-cpu.github.io/fantasy-stars-analyzer/).

## Run locally

From the repository root, start a local server with Python 3.

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open [the local app](http://127.0.0.1:8765/). Keep the server running while you use the app and press Ctrl+C to stop it. The localhost address has its own card collection. To move your collection between the public app and localhost, export a JSON backup under **Mer** and import it at the other address.

## Refresh NHL data and portraits

Run the commands below from the repository root in this order. Both commands need network access. The statistics download can take several minutes.

```sh
python3 scripts/update_nhl.py
python3 scripts/update_portraits.py
```

The first command updates the active `data/nhl-*.json` file with NHL statistics, current roster status, and available match history. It also writes `data/nhl-results-*.json` with official completed-game stats for saved lineup results. The second updates `assets/players/portraits.json` and the PNG files it references. Review the output for missing portrait IDs. The app shows initials for players whose portrait is unavailable.

On GitHub, **Uppdatera NHL-statistik** runs twice daily or can be started with **Run workflow**. It refreshes statistics and portraits, commits the results, requests a GitHub Pages build, and checks that the public data file reaches the generated timestamp. **Publicera spelarporträtt** can rebuild the image files from the saved manifest. For new players or updated NHL sources, use the full NHL workflow.

## Change the active NHL season

1. Set `SEASONS` in `scripts/update_nhl.py` to the new eight-digit NHL season ID, such as `20272028` for 2027/28. The portrait updater uses the first season listed by default.
2. Run both refresh commands above. Confirm that the new season has enough regular-season data to pass the updater's validation and that the new JSON file contains players, team or roster status, and available form history.
3. Update the season selector in `index.html`. In `.github/workflows/update-nhl.yml`, update the staged statistics and results paths and the paths used to verify the public files. Keep prior season files in the repository.
4. Start the app locally. Confirm the selected season loads and check Top 50, Scout, Form and portraits. Publish the season changes together, then check the public file and follow the release checks below.

## Release checks

For each app release, update the version in the HTML title, the heading and the Apple web app title in `index.html`. Use patch versions for smaller updates (4.1.1, 4.1.2, and so on). Ask Mattias for explicit approval before moving to 5.0. Add a release entry with the same version and a short Swedish summary to the `appReleases` JSON block. Keep previous entries so users can see what changed when skipping a version. Automatic NHL data refreshes keep the current app version.

1. Start from an up-to-date copy of GitHub `main`. Review local changes with `git status` and preserve any work in progress before bringing in upstream changes. Commit only the intended release files and publish them to `main`.
2. Wait for GitHub Pages to serve the new version at the existing URL. For an NHL data release, compare the season file's `updated` value on Pages and on `main`. Check the NHL workflow if the values differ after deployment.
3. For UI changes, exercise the affected flow in WebKit at iPhone width against the public URL. Then verify the same flow in Safari on the user's iPhone. If the app is launched from a Home Screen icon, verify that entry point too. For portrait releases, confirm that a player image loads, opens at full size, and closes.
4. Record the published commit, how the change was tested, and the result of the physical iPhone check. A WebKit test on the Mac can cover layout and interactions. The device check stays pending until the user confirms it.
