import json
import subprocess
import csv
import re
from collections import defaultdict

DUKE_ID = '150'

def classify_shot(play):
    """Classify a single shot attempt."""
    text = play.get('text', '')
    tl = text.lower()
    x = play.get('coordinate', {}).get('x', 25) #classify state by coordinates
    y = play.get('coordinate', {}).get('y', 0)
    made = play.get('scoringPlay', False)
    
    if 'free throw' in tl:
        return None
    
    made_str = 'MAKE' if made else 'MISS'
    
    # extract player name
    m = re.match(r'^([A-Za-z\s]+?)\s+(makes|misses)', text)
    player = m.group(1).strip() if m else 'Unknown'
    
    # close shots: dunks, layups, tip-ins
    is_close = any(w in tl for w in ['dunk', 'layup', 'tip in', 'tip-in'])
    if is_close:
        if 'dunk' in tl:
            desc = 'Dunk'
        elif 'tip in' in tl or 'tip-in' in tl:
            desc = 'Tip-in layup'
        else:
            desc = 'Layup'
        return {
            'category': f'1_{made_str}',
            'description': desc,
            'player': player,
            'made': made,
            'x': x, 'y': y
        }
    
    # three pointers
    is_three = 'three point' in tl
    if is_three:
        num = 4 if x < 25 else 5
        side = 'Left' if x < 25 else 'Right'
        return {
            'category': f'{num}_{made_str}',
            'description': f'{side} three pointer',
            'player': player,
            'made': made,
            'x': x, 'y': y
        }
    
    # mid range jump shots
    num = 2 if x <= 25 else 3
    side = 'Left' if x <= 25 else 'Right'
    return {
        'category': f'{num}_{made_str}',
        'description': f'{side} jump shot',
        'player': player,
        'made': made,
        'x': x, 'y': y
    }

# get all game IDs from ESPN schedule page
print("Fetching Duke schedule page...")
url = 'https://www.espn.com/mens-college-basketball/team/schedule/_/id/150'
result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=15)
game_ids = sorted(set(re.findall(r'gameId/(\d+)', result.stdout)))

print(f"Found {len(game_ids)} games\n")

# process each game
all_shots = defaultdict(list)

for i, game_id in enumerate(game_ids, 1):
    print(f"[{i:2d}/{len(game_ids)}] {game_id}...", end=' ', flush=True)
    
    try:
        # fetch play-by-play data from ESPN API
        url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}'
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"SKIP ({e})")
        continue
    
    # get game info
    comp = data.get('header', {}).get('competitions', [{}])[0]
    competitors = comp.get('competitors', [])
    if len(competitors) >= 2:
        team1 = competitors[0].get('team', {}).get('displayName', 'Team1')
        team2 = competitors[1].get('team', {}).get('displayName', 'Team2')
        opponent = team2 if 'Duke' in team1 else team1
        game_name = f"Duke vs {opponent}"
    else:
        game_name = "Unknown Game"
    
    game_date = comp.get('date', '').split('T')[0] if comp.get('date') else 'Unknown'
    
    # extract all Duke field goal attempts
    plays = data.get('plays', [])
    shot_count = 0
    
    for play in plays:
        if play.get('team', {}).get('id', '') != DUKE_ID:
            continue
        if not play.get('shootingPlay', False):
            continue
        
        shot = classify_shot(play)
        if shot:
            period = play.get('period', {}).get('number', '')
            clock = play.get('clock', {}).get('displayValue', '')
            shot['game'] = game_name
            shot['date'] = game_date
            shot['period'] = period
            shot['time'] = clock
            all_shots[shot['player']].append(shot)
            shot_count += 1
    
    print(f"{shot_count} FG")

# write per-player CSVs
print(f"\nWriting {len(all_shots)} player CSVs...")

for player, shots in sorted(all_shots.items()):
    filename = f"{player.replace(' ', '_')}_2025_2026_season.csv"
    filepath = f"/output/path/{filename}"
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Description', 'Game', 'Date', 'Period', 'Time', 'X', 'Y'])
        for shot in shots:
            writer.writerow([
                shot['category'],
                shot['description'],
                shot['game'],
                shot['date'],
                shot['period'],
                shot['time'],
                round(shot['x'], 1),
                round(shot['y'], 1)
            ])
