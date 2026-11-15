
#!/usr/bin/env python3
"""Fetch NHL regular-season skater stats into static JSON for GitHub Pages."""
import json
import pathlib
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
OUT.mkdir(exist_ok=True)
BASE = 'https://api.nhle.com/stats/rest/en/skater/'


def get_report(report, season):
    params = urllib.parse.urlencode({
        'isAggregate': 'true', 'isGame': 'false',
        'cayenneExp': f'seasonId={season} and gameTypeId=2',
        'limit': '-1', 'start': '0'
    })
    url = BASE + report + '?' + params
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'FantasyStarsAnalyzer/3.1 (GitHub Actions; stats cache)',
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=40) as response:
                payload = json.load(response)
            rows = payload.get('data')
            if not isinstance(rows, list) or not rows:
                raise ValueError(f'Empty or invalid {report} response')
            return rows
        except Exception as exc:
            last_error = exc
            print(f'{report} {season} attempt {attempt+1} failed: {exc}', flush=True)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'Cannot fetch {report} for {season}: {last_error}')


def number(row, *names):
    for name in names:
        if row.get(name) is not None:
            return row[name]
    return None


def normalize(season):
    summary = get_report('summary', season)
    realtime = get_report('realtime', season)
    real_by_id = {str(r.get('playerId')): r for r in realtime}
    players = []
    for s in summary:
        pid = s.get('playerId')
        r = real_by_id.get(str(pid))
        if not r:
            continue  # No zero-filling missing realtime statistics.
        hits = number(r, 'hits')
        blocks = number(r, 'blockedShotAttempts', 'blockedShots', 'blocks')
        if hits is None or blocks is None:
            raise ValueError('NHL realtime report lacks hits/blocked shots fields')
        games = number(s, 'gamesPlayed', 'games')
        if not games or not s.get('skaterFullName'):
            continue
        players.append({
            'id': pid,
            'name': s['skaterFullName'],
            'team': s.get('teamAbbrevs', ''),
            'pos': s.get('positionCode', ''),
            'games': games,
            'goals': number(s, 'goals') or 0,
            'assists': number(s, 'assists') or 0,
            'shots': number(s, 'shots') or 0,
            'hits': hits,
            'blocks': blocks
        })
    if len(players) < 100:
        raise ValueError(f'Only {len(players)} skaters matched: refusing to publish incomplete data')
    result = {'season': season, 'updated': datetime.now(timezone.utc).isoformat(), 'players': players}
    target = OUT / f'nhl-{season}.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    temp.replace(target)
    print(f'Wrote {target}: {len(players)} skaters', flush=True)


if __name__ == '__main__':
    for season_id in ('20262027', '20252026'):
        normalize(season_id)
