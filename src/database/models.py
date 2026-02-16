"""
SQLAlchemy models for SoccerGPT database schema.
Optimized for Football-Data.org v4 API compatibility.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class League(Base):
    """Represents a football league or tournament competition."""
    __tablename__ = 'leagues'
    
    # Update with competitions endpoint
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10))
    country = Column(String(50))
    emblem_url = Column(String(255))
    current_season_start = Column(Date)
    current_season_end = Column(Date)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")
    standings = relationship("Standing", back_populates="league")
    
    def __repr__(self):
        return f"<League(name='{self.name}', code='{self.code}')>"

class Team(Base):
    """Represents a football team."""
    __tablename__ = 'teams'
    
    # Update with competitions/league_code/teams endpoint
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(50))
    tla = Column(String(3))
    crest_url = Column(String(255))
    venue = Column(String(100))
    founded = Column(Integer)
    website = Column(String(255))
    league_id = Column(Integer, ForeignKey('leagues.id'))
    league_name = Column(String(100))
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")
    standings = relationship("Standing", back_populates="team")
    
    def __repr__(self):
        return f"<Team(name='{self.name}', tla='{self.tla}')>"

class Player(Base):
    """Represents a player."""
    __tablename__ = 'players'
    
    # Update with competitions/league_code/teams/scorers endpoint
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    position = Column(String(50))
    date_of_birth = Column(Date)
    nationality = Column(String(50))
    shirt_number = Column(Integer)
    team_id = Column(Integer, ForeignKey('teams.id'))
    team_name = Column(String(100))
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    matches_played = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="players")

class Match(Base):
    """Represents a match."""
    __tablename__ = 'matches'
    
    # Update with competitions/league_code/matches endpoint
    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True, nullable=False, index=True)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)
    league_name = Column(String(100))
    season = Column(String(20))
    matchday = Column(Integer)
    stage = Column(String(50))
    group = Column(String(20))
    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    home_team_name = Column(String(100))
    away_team_name = Column(String(100))
    utc_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20)) 
    duration = Column(String(20))
    winner = Column(String(20))
    home_score_full_time = Column(Integer)
    away_score_full_time = Column(Integer)
    home_score_half_time = Column(Integer)
    away_score_half_time = Column(Integer)
    referee = Column(String(100))
    venue = Column(String(100))
    
    # For cup games
    home_score_regular_time = Column(Integer)
    away_score_regular_time = Column(Integer)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

class Standing(Base):
    """Represents standings with group and type for tournaments."""
    __tablename__ = 'standings'
    
    # Update with competitions/league_code/standings endpoint
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)
    league_name = Column(String(100))
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    team_name = Column(String(100))
    season = Column(String(20))
    group = Column(String(20))
    type = Column(String(20))
    position = Column(Integer, nullable=False)
    played_games = Column(Integer, default=0)
    won = Column(Integer, default=0)
    draw = Column(Integer, default=0)
    lost = Column(Integer, default=0)
    points = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)
    form = Column(String(10))
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="standings")
    team = relationship("Team", back_populates="standings")