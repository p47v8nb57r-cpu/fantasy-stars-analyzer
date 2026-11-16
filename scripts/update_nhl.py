
#!/usr/bin/env python3
"""Fetch NHL stats, last-five-game form and current teams."""

import json
import pathlib
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)

STATS_BASE = "https://api.nhle.com/stats/rest/en/skater/"
WEB_BASE = "https://api-web.nhle.com/v1"

HEADERS = {
    "User-Agent": "FantasyStarsAnalyzer/3.6 (GitHub Actions)",
    "Accept": "application/json",
}

SEASONS = ("20262027",)
FORM_LIMIT = 5
REQUEST_DELAY = 0.08


def fetch_json(url):
    last_error = None

    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url,
                headers=HEADERS,
            )

            with urllib.request.urlopen(
                req,
                timeout=40,
            ) as response:
                return json.load(response)

        except Exception as exc:
            last_error = exc

            print(
                f"Request failed ({attempt + 1}/4): "
                f"{url}: {exc}",
                flush=True,
            )

            if attempt < 3:
                time.sleep(2 * (attempt + 1))

    raise RuntimeError(
        f"Cannot fetch {url}: {last_error}"
    )


def get_report(report, season):
    params = urllib.parse.urlencode({
        "isAggregate": "true",
        "isGame": "false",
        "cayenneExp": (
            f"seasonId={season} and gameTypeId=2"
        ),
        "limit": "-1",
        "start": "0",
    })

    payload = fetch_json(
        STATS_BASE + report + "?" + params
    )

    rows = payload.get("data")

    if not isinstance(rows, list) or not rows:
        raise ValueError(
            f"Empty or invalid {report} response"
        )

    return rows


def number(row, *names):
    for name in names:
        if row.get(name) is not None:
            return row[name]

    return None


def localized(value):
    if isinstance(value, dict):
        return (
            value.get("default")
            or value.get("en")
            or ""
        )

    return value or ""


def get_current_teams():
    """Build player ID to current NHL team mapping."""

    payload = fetch_json(
        f"{WEB_BASE}/standings/now"
    )

    standings = payload.get("standings", [])

    if not standings:
        raise ValueError(
            "Could not retrieve NHL standings"
        )

    teams = {}

    for row in standings:
        abbrev = localized(
            row.get("teamAbbrev")
        )

        if not abbrev:
            continue

        try:
            roster = fetch_json(
                f"{WEB_BASE}/roster/{abbrev}/current"
            )

            for group in (
                "forwards",
                "defensemen",
                "goalies",
            ):
                for player in roster.get(group, []):
                    pid = player.get("id")

                    if pid is not None:
                        teams[str(pid)] = abbrev

        except Exception as exc:
            print(
                f"Roster unavailable for "
                f"{abbrev}: {exc}",
                flush=True,
            )

        time.sleep(REQUEST_DELAY)

    if len(teams) < 100:
        raise ValueError(
            "Too few current NHL team mappings"
        )

    print(
        f"Current NHL team mappings: "
        f"{len(teams)}",
        flush=True,
    )

    return teams


def get_game_log(player_id, season):
    """Get completed regular-season games."""

    url = (
        f"{WEB_BASE}/player/{player_id}/"
        f"game-log/{season}/2"
    )

    payload = fetch_json(url)

    games = payload.get("gameLog")

    if not isinstance(games, list):
        raise ValueError(
            f"Missing gameLog for player {player_id}"
        )

    return games


def get_game_stats(game_id):
    """Get hits and blocks for one NHL game."""

    params = urllib.parse.urlencode({
        "isAggregate": "false",
        "isGame": "true",
        "cayenneExp": f"gameId={game_id}",
        "limit": "-1",
        "start": "0",
    })

    payload = fetch_json(
        STATS_BASE + "realtime?" + params
    )

    rows = payload.get("data")

    if not isinstance(rows, list):
        raise ValueError(
            f"Invalid realtime data for game {game_id}"
        )

    result = {}

    for row in rows:
        pid = row.get("playerId")

        if pid is None:
            continue

        hits = number(
            row,
            "hits",
        )

        blocks = number(
            row,
            "blockedShotAttempts",
            "blockedShots",
            "blocks",
        )

        if hits is None or blocks is None:
            raise ValueError(
                f"Missing hits/blocks for "
                f"game {game_id}, player {pid}"
            )

        result[str(pid)] = {
            "hits": hits,
            "blocks": blocks,
        }

    return result


def build_form(players, season):
    """Attach five latest complete games to each player."""

    game_logs = {}
    needed_games = set()

    print(
        f"Fetching game logs for "
        f"{len(players)} players...",
        flush=True,
    )

    for index, player in enumerate(
        players,
        start=1,
    ):
        pid = str(player["id"])

        try:
            games = get_game_log(
                pid,
                season,
            )

        except Exception as exc:
            print(
                f"Game log unavailable for "
                f"{pid}: {exc}",
                flush=True,
            )

            games = []

        games = sorted(
            (
                g for g in games
                if g.get("gameId")
                and g.get("gameDate")
            ),
            key=lambda g: (
                g["gameDate"],
                g["gameId"],
            ),
            reverse=True,
        )[:FORM_LIMIT]

        game_logs[pid] = games

        for game in games:
            needed_games.add(
                str(game["gameId"])
            )

        if index % 100 == 0:
            print(
                f"Game logs: "
                f"{index}/{len(players)}",
                flush=True,
            )

        time.sleep(REQUEST_DELAY)

    print(
        f"Fetching realtime stats for "
        f"{len(needed_games)} unique games...",
        flush=True,
    )

    realtime_by_game = {}

    for index, game_id in enumerate(
        sorted(needed_games),
        start=1,
    ):
        try:
            realtime_by_game[game_id] = (
                get_game_stats(game_id)
            )

        except Exception as exc:
            print(
                f"Realtime unavailable for "
                f"game {game_id}: {exc}",
                flush=True,
            )

            realtime_by_game[game_id] = {}

        if index % 100 == 0:
            print(
                f"Realtime games: "
                f"{index}/{len(needed_games)}",
                flush=True,
            )

        time.sleep(REQUEST_DELAY)

    complete_players = 0

    for player in players:
        pid = str(player["id"])
        form = []

        for game in game_logs.get(pid, []):
            game_id = str(game["gameId"])

            realtime = (
                realtime_by_game
                .get(game_id, {})
                .get(pid)
            )

            if realtime is None:
                continue

            goals = number(
                game,
                "goals",
            )

            assists = number(
                game,
                "assists",
            )

            shots = number(
                game,
                "shots",
            )

            if (
                goals is None
                or assists is None
                or shots is None
            ):
                continue

            entry = {
                "gameId": game["gameId"],
                "date": game["gameDate"],
                "opponent": localized(
                    game.get("opponentAbbrev")
                ),
                "homeAway": game.get(
                    "homeRoadFlag",
                    "",
                ),
                "goals": goals,
                "assists": assists,
                "shots": shots,
                "hits": realtime["hits"],
                "blocks": realtime["blocks"],
            }

            entry["fptsBase"] = (
                goals * 7
                + assists * 4
                + shots
                + realtime["hits"]
                + realtime["blocks"]
            )

            entry["fptsGold"] = (
                goals * 10
                + assists * 7
                + shots * 4
                + realtime["hits"] * 4
                + realtime["blocks"] * 4
            )

            form.append(entry)

        form.reverse()
        player["last5"] = form

        if form:
            complete_players += 1

            player["formAvgBase"] = round(
                sum(
                    g["fptsBase"]
                    for g in form
                ) / len(form),
                2,
            )

            player["formAvgGold"] = round(
                sum(
                    g["fptsGold"]
                    for g in form
                ) / len(form),
                2,
            )

        else:
            player["formAvgBase"] = None
            player["formAvgGold"] = None

    print(
        f"Players with available game form: "
        f"{complete_players}/{len(players)}",
        flush=True,
    )


def normalize(season):
    print(
        f"Processing NHL season {season}...",
        flush=True,
    )

    summary = get_report(
        "summary",
        season,
    )

    realtime = get_report(
        "realtime",
        season,
    )

    print(
        "Fetching current NHL team rosters...",
        flush=True,
    )

    current_teams = get_current_teams()

    real_by_id = {
        str(row.get("playerId")): row
        for row in realtime
    }

    players = []

    for s in summary:
        pid = s.get("playerId")

        r = real_by_id.get(
            str(pid)
        )

        if not r:
            continue

        hits = number(
            r,
            "hits",
        )

        blocks = number(
            r,
            "blockedShotAttempts",
            "blockedShots",
            "blocks",
        )

        if hits is None or blocks is None:
            raise ValueError(
                "NHL realtime report lacks "
                "hits/blocked shots fields"
            )

        games = number(
            s,
            "gamesPlayed",
            "games",
        )

        if (
            not games
            or not s.get("skaterFullName")
        ):
            continue

        team = current_teams.get(
            str(pid),
            "",
        )

        players.append({
            "id": pid,
            "name": s["skaterFullName"],
            "team": team,
            "pos": s.get(
                "positionCode",
                "",
            ),
            "games": games,
            "goals": number(
                s,
                "goals",
            ) or 0,
            "assists": number(
                s,
                "assists",
            ) or 0,
            "shots": number(
                s,
                "shots",
            ) or 0,
            "hits": hits,
            "blocks": blocks,
        })

    if len(players) < 100:
        raise ValueError(
            f"Only {len(players)} skaters matched: "
            "refusing to publish incomplete data"
        )

    with_team = sum(
        bool(p["team"])
        for p in players
    )

    print(
        f"Players with current team: "
        f"{with_team}/{len(players)}",
        flush=True,
    )

    build_form(
        players,
        season,
    )

    result = {
        "season": season,
        "updated": datetime.now(
            timezone.utc
        ).isoformat(),
        "players": players,
    }

    target = (
        OUT / f"nhl-{season}.json"
    )

    temp = target.with_suffix(
        ".tmp"
    )

    temp.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    temp.replace(target)

    print(
        f"Wrote {target}: "
        f"{len(players)} skaters",
        flush=True,
    )


if __name__ == "__main__":
    for season_id in SEASONS:
        normalize(season_id)
