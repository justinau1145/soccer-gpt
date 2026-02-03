import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, League, Team, Player, Match, Standing

load_dotenv()


# Configurations
API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
BASE_URL = 'https://api.football-data.org/v4'
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///data/soccer.db')
HEADERS = {'X-Auth-Token': API_KEY}

# Validate API key
if not API_KEY:
    raise ValueError("FOOTBALL_DATA_API_KEY not found in .env file. Please add your API key.")

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def fetch_data(endpoint: str):
    """Fetches data from the API given a specific endpoint."""
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit hit. Waiting 60 seconds...")
        time.sleep(60)
        return fetch_data(endpoint)
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def sync_leagues():
    """Syncs available competitions."""
    data = fetch_data('competitions')
    if not data: return
    
    for comp in data['competitions']:
        # Checks for existing leagues
        existing_league = session.query(League).filter_by(api_id=comp['id']).first()
        
        if existing_league:
            existing_league.name = comp['name']
            existing_league.code = comp['code']
            existing_league.country = comp['area']['name']
        else:
            league = League(
                api_id=comp['id'],
                name=comp['name'],
                code=comp['code'],
                country=comp['area']['name']
            )
            session.add(league)
    
    session.commit()
    print("Leagues synced.")

def sync_teams(league_code):
    """Syncs teams for a specific league."""
    data = fetch_data(f'competitions/{league_code}/teams')
    if not data: return
    
    # Get the local league ID
    league = session.query(League).filter_by(code=league_code).first()
    if not league:
        print(f"League {league_code} not found. Run sync_leagues() first.")
        return
    
    for t in data['teams']:
        # Checks for existing teams
        existing_team = session.query(Team).filter_by(api_id=t['id']).first()
        
        if existing_team:
            existing_team.name = t['name']
            existing_team.short_name = t['shortName']
            existing_team.tla = t['tla']
            existing_team.venue = t['venue']
            existing_team.league_id = league.id
        else:
            team = Team(
                api_id=t['id'],
                name=t['name'],
                short_name=t['shortName'],
                tla=t['tla'],
                venue=t['venue'],
                league_id=league.id
            )
            session.add(team)
    
    session.commit()
    print(f"Teams for {league_code} synced.")

def sync_matches(league_code):
    """Syncs matches for a specific league."""
    data = fetch_data(f'competitions/{league_code}/matches')
    if not data: return
    
    league = session.query(League).filter_by(code=league_code).first()
    
    # Create team lookup map
    team_map = {t.api_id: t.id for t in session.query(Team).filter_by(league_id=league.id).all()}
    
    for m in data['matches']:
        local_home_id = team_map.get(m['homeTeam']['id'])
        local_away_id = team_map.get(m['awayTeam']['id'])
        
        dt_object = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
        
        # Check for existing matches
        existing_match = session.query(Match).filter_by(api_id=m['id']).first()
        
        if existing_match:
            existing_match.league_id = league.id
            existing_match.season = str(m['season']['startDate'][:4])
            existing_match.matchday = m.get('matchday')
            existing_match.stage = m.get('stage')
            existing_match.group = m.get('group')
            existing_match.home_team_id = local_home_id
            existing_match.away_team_id = local_away_id
            existing_match.utc_date = dt_object
            existing_match.status = m['status']
            existing_match.duration = m['score'].get('duration')
            existing_match.winner = m['score'].get('winner')
            existing_match.home_score_full_time = m['score']['fullTime'].get('home')
            existing_match.away_score_full_time = m['score']['fullTime'].get('away')
            existing_match.home_score_half_time = m['score']['halfTime'].get('home')
            existing_match.away_score_half_time = m['score']['halfTime'].get('away')
            existing_match.home_score_regular_time = m['score'].get('regularTime', {}).get('home')
            existing_match.away_score_regular_time = m['score'].get('regularTime', {}).get('away')
            existing_match.referee = m['referees'][0]['name'] if m.get('referees') else None
            existing_match.venue = m.get('venue')
        else:
            match = Match(
                api_id=m['id'],
                league_id=league.id,
                season=str(m['season']['startDate'][:4]),
                matchday=m.get('matchday'),
                stage=m.get('stage'),
                group=m.get('group'),
                home_team_id=local_home_id,
                away_team_id=local_away_id,
                utc_date=dt_object,
                status=m['status'],
                duration=m['score'].get('duration'),
                winner=m['score'].get('winner'),
                home_score_full_time=m['score']['fullTime'].get('home'),
                away_score_full_time=m['score']['fullTime'].get('away'),
                home_score_half_time=m['score']['halfTime'].get('home'),
                away_score_half_time=m['score']['halfTime'].get('away'),
                home_score_regular_time=m['score'].get('regularTime', {}).get('home'),
                away_score_regular_time=m['score'].get('regularTime', {}).get('home'),
                referee=m['referees'][0]['name'] if m.get('referees') else None,
                venue=m.get('venue')
            )
            session.add(match)
    
    session.commit()
    print(f"Matches for {league_code} synced successfully.")

def sync_standings(league_code):
    """Syncs standings for a specific league."""
    data = fetch_data(f'competitions/{league_code}/standings')
    if not data: return
    
    league = session.query(League).filter_by(code=league_code).first()
    if not league:
        print(f"League {league_code} not found. Run sync_leagues() first.")
        return
    
    # Create team lookup map
    team_map = {t.api_id: t.id for t in session.query(Team).filter_by(league_id=league.id).all()}
    
    for standing_type in data['standings']:
        standing_group = standing_type.get('group')  # For group stages
        standing_table_type = standing_type.get('type', 'TOTAL')
        
        for entry in standing_type['table']:
            team_api_id = entry['team']['id']
            local_team_id = team_map.get(team_api_id)
            
            if not local_team_id:
                continue
            
            # Query for existing standing
            existing_standing = session.query(Standing).filter_by(
                league_id=league.id,
                team_id=local_team_id,
                type=standing_table_type,
                group=standing_group
            ).first()
            
            if existing_standing:
                existing_standing.season = str(data['season']['startDate'][:4])
                existing_standing.position = entry['position']
                existing_standing.played_games = entry['playedGames']
                existing_standing.won = entry['won']
                existing_standing.draw = entry['draw']
                existing_standing.lost = entry['lost']
                existing_standing.points = entry['points']
                existing_standing.goals_for = entry['goalsFor']
                existing_standing.goals_against = entry['goalsAgainst']
                existing_standing.goal_difference = entry['goalDifference']
                existing_standing.form = entry.get('form')
            else:
                standing = Standing(
                    league_id=league.id,
                    team_id=local_team_id,
                    season=str(data['season']['startDate'][:4]),
                    group=standing_group,
                    type=standing_table_type,
                    position=entry['position'],
                    played_games=entry['playedGames'],
                    won=entry['won'],
                    draw=entry['draw'],
                    lost=entry['lost'],
                    points=entry['points'],
                    goals_for=entry['goalsFor'],
                    goals_against=entry['goalsAgainst'],
                    goal_difference=entry['goalDifference'],
                    form=entry.get('form')
                )
                session.add(standing)
    
    session.commit()
    print(f"Standings for {league_code} synced successfully.")

def sync_top_scorers(league_code):
    """Syncs top scorers for a specific league."""
    data = fetch_data(f'competitions/{league_code}/scorers')
    if not data: return
    
    league = session.query(League).filter_by(code=league_code).first()
    if not league:
        print(f"League {league_code} not found. Run sync_leagues() first.")
        return
    
    # Create team lookup map
    team_map = {t.api_id: t.id for t in session.query(Team).filter_by(league_id=league.id).all()}
    
    for scorer in data['scorers']:
        player_data = scorer['player']
        team_api_id = scorer['team']['id']
        local_team_id = team_map.get(team_api_id)
        
        if not local_team_id:
            continue
        
        # Query for existing player
        existing_player = session.query(Player).filter_by(api_id=player_data['id']).first()
        
        if existing_player:
            existing_player.name = player_data['name']
            existing_player.position = player_data.get('position')
            existing_player.nationality = player_data.get('nationality')
            existing_player.team_id = local_team_id
            existing_player.goals = scorer.get('goals', 0)
            existing_player.assists = scorer.get('assists', 0)
            existing_player.matches_played = scorer.get('playedMatches', 0)
        else:
            player = Player(
                api_id=player_data['id'],
                name=player_data['name'],
                position=player_data.get('position'),
                date_of_birth=datetime.strptime(player_data['dateOfBirth'], "%Y-%m-%d").date() if player_data.get('dateOfBirth') else None,
                nationality=player_data.get('nationality'),
                team_id=local_team_id,
                goals=scorer.get('goals', 0),
                assists=scorer.get('assists', 0),
                matches_played=scorer.get('playedMatches', 0)
            )
            session.add(player)
    
    session.commit()
    print(f"Top scorers for {league_code} synced successfully.")


if __name__ == "__main__":
    # Initialize DB tables if they don't exist
    Base.metadata.create_all(engine)
    
    sync_leagues()

    # Test syncing with premier league (PL)
    sync_teams('PL')
    sync_matches('PL')
    sync_standings('PL')
    sync_top_scorers('PL')