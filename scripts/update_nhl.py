
#!/usr/bin/env python3
"""Fetch NHL stats, last-five-game form and current teams."""

import json
import pathlib
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from nhl_availability import forecast_availability

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)

STATS_ROOT = "https://api.nhle.com/stats/rest/en/"
STATS_BASE = STATS_ROOT + "skater/"
WEB_BASE = "https://api-web.nhle.com/v1"

HEADERS = {
    "User-Agent": "FantasyStarsAnalyzer/3.6 (GitHub Actions)",
    "Accept": "application/json",
}

SEASONS = ("20262027",)
FORM_LIMIT = 5
REQUEST_DELAY = 0.08
REPORT_PAGE_SIZE = 100
NHL_TEAM_COUNT = 32


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
    rows = get_paged_report("skater/" + report, season, ("playerId",))
    print(f"{report}: {len(rows)} skaters", flush=True)
    return rows


def get_paged_report(report, season, key_fields, *, games=False):
    filters = {
        "isAggregate": "false" if games else "true",
        "isGame": "true" if games else "false",
        "cayenneExp": (
            f"seasonId={season} and gameTypeId=2"
        ),
        "limit": REPORT_PAGE_SIZE,
        "sort": json.dumps([{"property": key, "direction": "ASC"} for key in key_fields]),
    }
    rows = []
    seen_ids = set()
    total = None

    while total is None or len(rows) < total:
        params = urllib.parse.urlencode({**filters, "start": len(rows)})
        payload = fetch_json(STATS_ROOT + report + "?" + params)
        page = payload.get("data")
        reported_total = payload.get("total")
        if (
            not isinstance(page, list)
            or not page
            or type(reported_total) is not int
            or reported_total < len(rows) + len(page)
        ):
            raise ValueError(f"Invalid {report} page at offset {len(rows)}")
        if total is not None and reported_total != total:
            raise ValueError(f"{report} total changed during pagination")
        total = reported_total

        for row in page:
            key = tuple(row.get(field) for field in key_fields)
            if None in key or key in seen_ids:
                raise ValueError(f"Missing or repeated row key in {report}: {key}")
            seen_ids.add(key)
        rows.extend(page)

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


def get_current_teams(standings):
    """Build player ID to current NHL team mapping."""

    abbreviations = [localized(row.get("teamAbbrev")) for row in standings]
    if (
        len(abbreviations) != NHL_TEAM_COUNT
        or len(set(abbreviations)) != NHL_TEAM_COUNT
        or not all(abbreviations)
    ):
        raise ValueError(
            f"Expected {NHL_TEAM_COUNT} distinct NHL teams in standings"
        )

    teams = {}

    for abbrev in abbreviations:
        roster = fetch_json(f"{WEB_BASE}/roster/{abbrev}/current")
        for group in ("forwards", "defensemen", "goalies"):
            players = roster.get(group)
            if not isinstance(players, list) or not players:
                raise ValueError(f"Incomplete roster for {abbrev}: missing {group}")
            for player in players:
                pid = player.get("id")
                if pid is None:
                    raise ValueError(f"Missing player ID in {abbrev} roster")
                pid = str(pid)
                if pid in teams:
                    raise ValueError(
                        f"Repeated player {pid} in NHL rosters: {teams[pid]}, {abbrev}"
                    )
                teams[pid] = abbrev

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
        games = game_logs.get(pid, [])
        player["lastPlayed"] = games[0]["gameDate"] if games else None

        for game in games:
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


def scheduled_games(days, season):
    for day in days:
        for game in day.get("games", []):
            if (
                str(game.get("season")) != season
                or game.get("gameType") != 2
                or game.get("gameScheduleState") in ("PPD", "CNCL")
            ):
                continue
            home = localized(game.get("homeTeam", {}).get("abbrev"))
            away = localized(game.get("awayTeam", {}).get("abbrev"))
            start = game.get("startTimeUTC")
            if home and away and start and day.get("date"):
                yield {
                    "id": game.get("id"), "date": day["date"], "start": start, "home": home, "away": away,
                    "state": game.get("gameState", ""),
                }, game


def get_lineup_data(season, standings, players=()):
    schedule = fetch_json(f"{WEB_BASE}/schedule/now")
    days = schedule.get("gameWeek")
    if not isinstance(days, list):
        raise ValueError("NHL schedule has no gameWeek")

    games = []
    previews = []
    for match, game in scheduled_games(days, season):
        games.append(match)
        away_nick = localized(game["awayTeam"].get("commonName"))
        home_nick = localized(game["homeTeam"].get("commonName"))
        if away_nick and home_nick:
            previews.append({
                **match,
                "awayNick": away_nick, "homeNick": home_nick,
                "awayName": f'{localized(game["awayTeam"].get("placeName"))} {away_nick}',
                "homeName": f'{localized(game["homeTeam"].get("placeName"))} {home_nick}',
            })

    scout_games = []
    if games:
        for _ in range(2):
            next_date = schedule.get("nextStartDate")
            if not next_date:
                break
            try:
                schedule = fetch_json(f"{WEB_BASE}/schedule/{next_date}")
                scout_games.extend(match for match, _ in scheduled_games(schedule["gameWeek"], season))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                print(f"::warning::Extended NHL schedule could not be read: {exc}", flush=True)
                break

    defense = {}
    total_games = 0
    total_goals = 0
    for row in standings:
        if str(row.get("seasonId")) != season or row.get("gameTypeId") != 2:
            continue
        team = localized(row.get("teamAbbrev"))
        played = row.get("gamesPlayed")
        allowed = row.get("goalAgainst")
        if team and isinstance(played, int) and played > 0 and isinstance(allowed, int) and allowed >= 0:
            defense[team] = allowed / played
            total_games += played
            total_goals += allowed

    availability = {}
    if players:
        try:
            availability = forecast_availability(previews, players, HEADERS)
        except (ValueError, TypeError) as exc:
            print(f"::warning::NHL availability reports could not be read: {exc}", flush=True)
    print(f"NHL availability: {len(availability)} match previews", flush=True)
    return {
        "updated": datetime.now(timezone.utc).isoformat(),
        "games": games,
        "scoutGames": scout_games,
        "availability": availability,
        "goalsAgainstPerGame": defense,
        "leagueGoalsAgainstPerGame": total_goals / total_games if total_games else None,
    }


def get_team_cards(season):
    reports = {
        "team/summary": ("gameId", "teamId"),
        "team/powerplay": ("gameId", "teamId"),
        "team/penaltykill": ("gameId", "teamId"),
        "goalie/summary": ("gameId", "playerId"),
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {
            report: pool.submit(get_paged_report, report, season, keys, games=True)
            for report, keys in reports.items()
        }
        rows = {report: job.result() for report, job in jobs.items()}

    key_for = lambda row: (row["gameId"], row["teamId"])
    pp = {key_for(row): row for row in rows["team/powerplay"]}
    pk = {key_for(row): row for row in rows["team/penaltykill"]}
    by_game = {}
    goalies = {}
    for row in rows["team/summary"]:
        by_game.setdefault(row["gameId"], []).append(row)
    for row in rows["goalie/summary"]:
        key = (row["gameId"], row.get("teamAbbrev"))
        totals = goalies.setdefault(key, {"saves": 0, "against": 0})
        totals["saves"] += row["saves"]
        totals["against"] += row["goalsAgainst"]

    teams = {}
    outcomes = {}
    for game, sides in by_game.items():
        if len(sides) != 2:
            raise ValueError(f"Missing opposing team in game {game}")
        for row, opponent in (sides, sides[::-1]):
            code = opponent["opponentTeamAbbrev"]
            key = key_for(row)
            our_goalies = goalies.get((game, code))
            their_goalies = goalies.get((game, row["opponentTeamAbbrev"]))
            if not code or key not in pp or key not in pk or our_goalies is None or their_goalies is None:
                raise ValueError(f"Incomplete team or goalie reports for {code} in game {game}")
            team = teams.setdefault(code, {"code": code, "name": row["teamFullName"], "results": []})
            result = {
                "date": row["gameDate"], "game": game, "win": row["wins"],
                "ppg": pp[key]["powerPlayGoalsFor"], "shg": pk[key]["shGoalsFor"],
                "against": our_goalies["against"], "shutout": row["teamShutouts"],
                "saves": our_goalies["saves"], "shotsFor": row["shotsForPerGame"],
                "goalsFor": their_goalies["against"], "ppAgainst": pk[key]["ppGoalsAgainst"],
                "shAgainst": pp[key]["shGoalsAgainst"], "scoreless": opponent["teamShutouts"],
            }
            team["results"].append(result)
            outcome = outcomes.setdefault(str(game), {"date": row["gameDate"], "teams": {}})
            outcome["teams"][code] = [result[key] for key in ("win", "ppg", "shg", "against", "shutout", "saves")]

    team_cards = []
    for team in teams.values():
        games = sorted(team.pop("results"), key=lambda row: (row["date"], row["game"]))
        team["games"] = len(games)
        team["season"] = {
            field: sum(row[field] for row in games) / len(games)
            for field in games[0] if field not in ("date", "game")
        }
        team["last5"] = games[-FORM_LIMIT:]
        team_cards.append(team)
    print(f"Team cards: {len(team_cards)} teams, {len(by_game)} completed games", flush=True)
    return sorted(team_cards, key=lambda team: team["code"]), outcomes


def get_result_skaters(game_id, season, team_codes):
    payload = fetch_json(f"{WEB_BASE}/gamecenter/{game_id}/boxscore")
    if (
        str(payload.get("id")) != game_id
        or str(payload.get("season")) != season
        or payload.get("gameType") != 2
        or payload.get("gameState") not in ("FINAL", "OFF")
    ):
        raise ValueError(f"No final boxscore for game {game_id}")
    skaters = {}
    codes = set()
    for side, groups in payload["playerByGameStats"].items():
        code = payload[side]["abbrev"]
        codes.add(code)
        players = groups["forwards"] + groups["defense"]
        if not players:
            raise ValueError(f"No skater rows for {code} in game {game_id}")
        for player in players:
            pid = str(player["playerId"])
            values = [player[field] for field in ("goals", "assists", "sog", "hits", "blockedShots")]
            if not pid.isdigit() or pid in skaters or any(type(value) is not int or value < 0 for value in values):
                raise ValueError(f"Incomplete skater statistics for {pid} in game {game_id}")
            skaters[pid] = values
    if codes != set(team_codes):
        raise ValueError(f"Team mismatch in game {game_id}")
    return skaters


def write_round_results(season, games):
    path = OUT / f"nhl-results-{season}.json"
    old = json.loads(path.read_text(encoding="utf-8")).get("games", {}) if path.exists() else {}
    refresh_since = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
    results = dict(old)

    def complete_game(game_id, entry):
        previous = old.get(game_id, {}).get("skaters")
        if previous and entry["date"] < refresh_since:
            return game_id, {**entry, "skaters": previous}
        try:
            return game_id, {**entry, "skaters": get_result_skaters(game_id, season, entry["teams"])}
        except (KeyError, TypeError, RuntimeError, ValueError) as exc:
            print(f"::warning::Skater outcome unavailable for {game_id}: {exc}", flush=True)
            return game_id, {**entry, "skaters": previous} if previous else None

    with ThreadPoolExecutor(max_workers=8) as pool:
        for game_id, entry in pool.map(lambda item: complete_game(*item), games.items()):
            if entry is not None:
                results[game_id] = entry
    output = {"season": season, "updated": datetime.now(timezone.utc).isoformat(), "games": results}
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(output, separators=(",", ":")), encoding="utf-8")
    temp.replace(path)
    print(f"Round results: {len(results)} games, {sum('skaters' in row for row in results.values())} with skaters", flush=True)


def refresh_team_cards(season):
    cards, results = get_team_cards(season)
    write_round_results(season, results)
    return cards


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

    standings = fetch_json(f"{WEB_BASE}/standings/now").get("standings", [])
    current_teams = get_current_teams(standings)

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
            "rosterStatus": "nhl" if team else "outside",
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
            f"Only {len(players)} skaters matched "
            f"(summary: {len(summary)}, realtime: {len(realtime)}): "
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

    for field, fetch in (
        ("lineup", lambda: get_lineup_data(season, standings, players)),
        ("teamCards", lambda: refresh_team_cards(season)),
    ):
        try:
            result[field] = fetch()
        except (ValueError, RuntimeError, KeyError, TypeError) as exc:
            print(f"::warning::Could not refresh {field}: {exc}", flush=True)
            if target.exists():
                previous = json.loads(target.read_text(encoding="utf-8"))
                if field in previous:
                    result[field] = previous[field]

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
