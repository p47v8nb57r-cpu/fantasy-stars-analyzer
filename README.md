# fantasy-stars-analyzer

## Release checks

The public app runs at [Fantasy Stars Analyzer](https://p47v8nb57r-cpu.github.io/fantasy-stars-analyzer/).

1. Start from an up-to-date copy of GitHub `main`. Review local changes with `git status` and preserve any work in progress before bringing in upstream changes. Commit only the intended release files and publish them to `main`.
2. Wait for GitHub Pages to serve the new version at the existing URL. For an NHL data release, compare the season file's `updated` value on Pages and on `main`. Check the NHL workflow if the values differ after deployment.
3. For UI changes, exercise the affected flow in WebKit at iPhone width against the public URL. Then verify the same flow in Safari on the user's iPhone. If the app is launched from a Home Screen icon, verify that entry point too. For portrait releases, confirm that a player image loads, opens at full size, and closes.
4. Record the published commit, how the change was tested, and the result of the physical iPhone check. A WebKit test on the Mac can cover layout and interactions. The device check stays pending until the user confirms it.

The NHL workflow runs twice daily. It requests a Pages build after saving new data and fails visibly in GitHub Actions if the public file does not reach the generated timestamp.
