"""Read matchup-specific availability statements from official NHL previews."""

import json
import re
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from html.parser import HTMLParser

MONTHS = (
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
)
NHL_NEWS = "https://www.nhl.com/news/"


def words(value):
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", value))


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.structured = False
        self.article = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.structured = dict(attrs).get("type") == "application/ld+json"

    def handle_endtag(self, tag):
        if tag == "script":
            self.structured = False

    def handle_data(self, text):
        if not self.structured:
            return
        try:
            item = json.loads(text)
        except ValueError:
            return
        if isinstance(item, dict) and isinstance(item.get("articleBody"), str):
            self.article = item


def preview_url(game):
    day = date.fromisoformat(game["date"])
    away = words(game["awayName"]).replace(" ", "-")
    home = words(game["homeName"]).replace(" ", "-")
    return f"{NHL_NEWS}{away}-{home}-game-preview-{MONTHS[day.month - 1]}-{day.day}-{day.year}"


def preview_body(url, headers):
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.geturl().rstrip("/") != url:
                return None
            parser = ArticleParser()
            parser.feed(response.read().decode("utf-8"))
            return parser.article
    except (OSError, UnicodeError):
        return None


OUT = re.compile(
    r"\b(?:will not play (?:tonight|today|in (?:this|the) game)|will not play$|"
    r"has been ruled out|is out indefinitely|"
    r"will miss (?:tonight|today|(?:this|the) game|his [a-z0-9]+ (?:straight|consecutive) game)|"
    r"will serve the [a-z0-9]+ of (?:his|a) [a-z0-9]+ game suspension)\b"
)
UNCERTAIN = re.compile(
    r"\b(?:game time decision|questionable|doubtful|day to day|decision on his status)\b"
)


def parse_availability(body, game, players):
    away, home = game["away"], game["home"]
    nicknames = {words(game["awayNick"]): away, words(game["homeNick"]): home}
    heading = re.search(r"^\s*##\s*([^\n]+)", body, re.MULTILINE)
    if not heading:
        return None
    teams = re.split(r"\s+at\s+", heading.group(1), maxsplit=1, flags=re.IGNORECASE)
    teams = [words(name.split("(")[0]) for name in teams]
    if teams != [words(game["awayNick"]), words(game["homeNick"])]:
        return None

    candidates = [p for p in players if p["team"] in (away, home)]
    status = {}
    report = []
    current_team = None
    in_report = False
    for line in body.splitlines():
        line = line.replace("*", "").strip()
        lower = line.lower()
        if words(line) == "status report":
            in_report = True
        elif in_report:
            if line.startswith("#"):
                break
            if line:
                report.append(line)
        elif lower.endswith(" projected lineup"):
            current_team = nicknames.get(words(line[:-len(" projected lineup")]))
        elif lower.startswith(("injured:", "scratched:")) and current_team:
            label, rest = line.split(":", 1)
            for name in re.sub(r"\([^)]*\)", "", rest).split(","):
                matches = [p for p in players if words(p["name"]) == words(name)]
                if len(matches) == 1 and matches[0]["team"] in (current_team, ""):
                    player = matches[0]
                    status[str(player["id"])] = {
                        "state": "uncertain", "reason": "injured" if label.lower() == "injured" else "scratch",
                        "name": player["name"],
                    }

    aliases = {}
    for player in players:
        if player not in candidates and str(player["id"]) not in status:
            continue
        name = words(player["name"])
        if not name:
            continue
        for alias in {name, name.split()[-1]}:
            aliases.setdefault(alias, []).append(player)
    for sentence in re.split(r"\.{2,}|…+|[.!?]\s+", " ".join(report)):
        normalized = words(sentence)
        subject = next((key for key in sorted(aliases, key=len, reverse=True)
                        if normalized.startswith(key + " ")), None)
        if not subject or len(aliases[subject]) != 1:
            continue
        rest = normalized[len(subject):].strip()
        match = OUT.search(rest)
        uncertain = UNCERTAIN.search(rest)
        evidence = match or uncertain
        if not evidence or len(rest[:evidence.start()].split()) > 12:
            continue
        player = aliases[subject][0]
        player_id = str(player["id"])
        reason = status.get(player_id, {}).get("reason")
        status[player_id] = {
            "state": "out" if match else "uncertain",
            "reason": "injured" if reason == "injured" else "explicit",
            "name": player["name"],
        }
    return status


def forecast_availability(games, players, headers):
    now = datetime.now(timezone.utc)
    upcoming = [g for g in games if g["state"] in ("FUT", "PRE") and g.get("id") and
                datetime.fromisoformat(g["start"].replace("Z", "+00:00")) > now]
    dates = set(sorted({g["date"] for g in upcoming})[:2])

    def report(game):
        url = preview_url(game)
        article = preview_body(url, headers)
        if not article:
            return None
        players_for_match = parse_availability(article["articleBody"], game, players)
        if players_for_match is None:
            return None
        return str(game["id"]), {
            "source": url, "updated": article.get("dateModified") or article.get("datePublished"),
            "players": players_for_match,
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return dict(result for result in pool.map(report, (g for g in upcoming if g["date"] in dates)) if result)
