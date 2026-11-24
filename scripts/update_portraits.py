#!/usr/bin/env python3
"""Download NHL portraits for the skaters in the app's season file."""

import concurrent.futures
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

from update_nhl import HEADERS, OUT, ROOT, SEASONS, WEB_BASE, fetch_json, localized

PORTRAITS = ROOT / "assets" / "players"
HEADSHOT = re.compile(r"https://assets\.nhle\.com/mugs/nhl/\d+/[A-Z]+/(\d+)\.png")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PLACEHOLDER_SHA256 = "ae3f3b1a9ba14a92c24dfe676a09505bd17436d56aee1d13ec580696ee141151"
GAGNE_PORTRAIT = (
    "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/"
    "unh.sidearmsports.com/images/2024/9/25/Alex_Gagne_DSC0008.png"
)


def is_player_portrait(url, player_id):
    match = HEADSHOT.fullmatch(url or "")
    return match is not None and match[1] == str(player_id)


def get_roster_portraits(season="current"):
    standings = fetch_json(f"{WEB_BASE}/standings/now")["standings"]
    teams = {localized(row["teamAbbrev"]) for row in standings}
    portraits = {}

    def roster(team):
        result = fetch_json(f"{WEB_BASE}/roster/{team}/{season}")
        return {
            player["id"]: player["headshot"]
            for group in ("forwards", "defensemen", "goalies")
            for player in result.get(group, [])
            if is_player_portrait(player.get("headshot"), player["id"])
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for entries in pool.map(roster, sorted(teams)):
            portraits.update(entries)
    return portraits


def is_portrait_image(content):
    return (
        content.startswith(PNG_SIGNATURE)
        and hashlib.sha256(content).hexdigest() != PLACEHOLDER_SHA256
    )


def download_portrait(url):
    if url == GAGNE_PORTRAIT:
        params = urllib.parse.urlencode({
            "url": url, "width": 336, "height": 336, "type": "png",
        })
        url = "https://images.sidearmdev.com/crop?" + params
    request = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def save_portrait(player_id, url, previous_sources):
    target = PORTRAITS / f"{player_id}.png"
    previous = previous_sources.get(str(player_id), "")
    if not target.is_file() or not is_portrait_image(target.read_bytes()):
        previous = ""

    try:
        if not url:
            profile = fetch_json(f"{WEB_BASE}/player/{player_id}/landing")
            url = profile.get("headshot")
        if not is_player_portrait(url, player_id) and (str(player_id), url) != ("8482942", GAGNE_PORTRAIT):
            return player_id, previous
        if previous == url:
            return player_id, url
        content = download_portrait(url)
        if not is_portrait_image(content):
            return player_id, previous
        temp = target.with_suffix(".tmp")
        temp.write_bytes(content)
        temp.replace(target)
        return player_id, url
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Portrait unavailable for {player_id}: {error}", flush=True)
        return player_id, previous


def main(season, from_manifest=False):
    data = json.loads((OUT / f"nhl-{season}.json").read_text(encoding="utf-8"))
    PORTRAITS.mkdir(parents=True, exist_ok=True)
    manifest = PORTRAITS / "portraits.json"
    previous_sources = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    roster_portraits = {} if from_manifest else get_roster_portraits()
    ids = sorted({int(pid) for pid in previous_sources} | {player["id"] for player in data["players"]})
    sources = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        jobs = [
            pool.submit(save_portrait, pid, roster_portraits.get(pid) or previous_sources.get(str(pid)), previous_sources)
            for pid in ids
        ]
        for completed, job in enumerate(concurrent.futures.as_completed(jobs), start=1):
            pid, url = job.result()
            if url and (PORTRAITS / f"{pid}.png").is_file():
                sources[str(pid)] = url
            if completed % 100 == 0:
                print(f"Checked {completed}/{len(ids)} portraits", flush=True)

        missing = [pid for pid in ids if str(pid) not in sources]
        if missing:
            start_year = int(season[:4])
            previous_season = f"{start_year - 1}{start_year}"
            print(f"Checking previous-season rosters for {len(missing)} players", flush=True)
            older_portraits = get_roster_portraits(previous_season)
            jobs = [
                pool.submit(save_portrait, pid, older_portraits[pid], previous_sources)
                for pid in missing if pid in older_portraits
            ]
            for job in concurrent.futures.as_completed(jobs):
                pid, url = job.result()
                if url:
                    sources[str(pid)] = url

    missing = [str(pid) for pid in ids if str(pid) not in sources]
    if missing:
        print(f"::warning::No portrait for NHL player IDs: {', '.join(missing)}", flush=True)
    if not sources or from_manifest and missing:
        raise RuntimeError(f"Portrait download incomplete: {len(sources)}/{len(ids)} available")
    temp = manifest.with_suffix(".tmp")
    temp.write_text(json.dumps(sources, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    temp.replace(manifest)
    print(f"Available portraits: {len(sources)}/{len(ids)}", flush=True)


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if arg != "--from-manifest"]
    main(args[0] if args else SEASONS[0], from_manifest="--from-manifest" in sys.argv)
