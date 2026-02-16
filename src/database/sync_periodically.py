from sync_statistics import sync_leagues, sync_teams, sync_top_scorers, sync_matches, sync_standings, engine
from models import Base
import time
import schedule


def sync_api(league_codes: list):
    """Syncs all leagues with a 60-second delay between each to respect rate limits."""
    Base.metadata.create_all(engine)
    
    sync_leagues()
    for i, league in enumerate(league_codes):
        if i > 0:
            time.sleep(60)
        
        print(f"Syncing {league}...")
        sync_teams(league)
        sync_top_scorers(league)
        sync_matches(league)
        sync_standings(league)


schedule.every(1).day.at("7:00").do(sync_api, league_codes=['PL', 'BL1', 'SA', 'FL1', 'PD'])

while True:
    schedule.run_pending()
    time.sleep(1)