import pandas as pd
import streamlit as st
from espn_api.football import League
from datetime import datetime

# TODO: How to we invalidate the cache if/when the user changes their "Settings"?
@st.cache_data
def get_all_matchup_stats(ESPN_S2, ESPN_SWID, ESPN_LEAGUE_ID, starting_year: int) -> pd.DataFrame:
    """
    Retrieves all-time matchup statistics for a fantasy football league from 2017 to 2024.
    This function iterates through each year and week, collects matchup data, and compiles it into a DataFrame.
    The data includes team names, scores, winning team, score difference, and whether the matchup was a playoff game.
    Returns:
        pd.DataFrame: A DataFrame containing all-time matchup statistics with columns:
            - year: The year of the matchup.
            - week: The week of the matchup.
            - home_team: The name of the home team.
            - home_score: The score of the home team.
            - away_team: The name of the away team (None if it was a bye week).
            - away_score: The score of the away team (0 if it was a bye week).
            - winning_team: The name of the winning team (or 'Tie' if the scores were equal).
            - score_diff: The absolute difference between the home and away scores.
            - is_playoff: Boolean indicating if the matchup was a playoff game.
            - winning_score: The score of the winning team.
            - losing_score: The score of the losing team.
    """
    all_matchup_stats = []

    def get_current_season() -> int:
        """
        Retrieves the current NFL season year.
        Returns:
            int: The current NFL season year.
        """
        current_year = datetime.now().year
        current_month = datetime.now().month

        # NFL season starts in September, so if it's before September, the season is the previous year
        if current_month < 9:
            return current_year - 1
        else:
            return current_year

    print('Starting year:', starting_year)
    print('Current  year:', get_current_season())
    current_season = get_current_season()

    for year in range(starting_year, current_season+1):
        league = League(
            espn_s2=ESPN_S2, 
            swid=ESPN_SWID, 
            league_id=ESPN_LEAGUE_ID, 
            year=year
        )
        print('Year:', league.year)

        for week in range(1, league.current_week+1):
            print('\tWeek:', week)
            box_scores = league.scoreboard(week)
            # league.box_scores() is only available from 2019+. box_scores has player data, which could be cool in the future. 
            # For now, league.scoreboard has all the basic top-level stats
            
            for box in box_scores:
                print('\t\tBox:', box.home_team.team_name, 'vs', '...')

                if not hasattr(box, 'away_team'):  # bye weeks
                    away_team = None
                    away_score = 0
                else:
                    away_team = box.away_team.owners[0]['firstName']
                    away_score = box.away_score

                home_team = box.home_team.owners[0]['firstName']  # For naming consistency on the rest of the code
                home_score = box.home_score

                if home_score > away_score:
                    winning_team = home_team
                elif home_score < away_score:
                    winning_team = away_team
                else:
                    winning_team = 'Tie'

                stats = {
                    'year': league.year,
                    'week': week,
                    'year_week': f"Y{league.year}_W{str(week).zfill(2)}",
                    'home_team': home_team,
                    'home_score': home_score,
                    'away_team': away_team,
                    'away_score': away_score,
                    'winning_team': winning_team,
                    'losing_team': home_team if winning_team == away_team else away_team,
                    'score_diff': abs(box.home_score - away_score),
                    'is_playoff': box.is_playoff
                }

                all_matchup_stats.append(stats)

    all_matchup_stats = pd.DataFrame(all_matchup_stats)
    all_matchup_stats.replace('Lol', 'Juliano', inplace=True)

    # For scatterplot
    all_matchup_stats['winning_score'] = all_matchup_stats.apply(
        lambda row: row['home_score'] if row['winning_team'] == row['home_team'] else row['away_score'], axis=1)
    all_matchup_stats['losing_score'] = all_matchup_stats.apply(
        lambda row: row['away_score'] if row['winning_team'] == row['home_team'] else row['home_score'], axis=1)
            
    return pd.DataFrame(all_matchup_stats)


def get_weekly_owner_stats(all_matchup_stats: pd.DataFrame) -> pd.DataFrame:
    # Create a running tally of the number of games each player has played and their cumulative wins
    weekly_player_perf = []
    all_teams = pd.concat([all_matchup_stats['home_team'], all_matchup_stats['away_team']]).unique()

    for team in all_teams:

        team_df = all_matchup_stats[(all_matchup_stats['home_team'] == team) | (all_matchup_stats['away_team'] == team)]
        team_df = team_df.sort_values(by=['year', 'week'])
        
        cumulative_wins = 0
        cumulative_games = 0

        for _, row in team_df.iterrows():
            cumulative_games += 1
            if row['winning_team'] == team:
                cumulative_wins += 1

            weekly_player_perf.append({
                # Keys
                'year': row['year'],
                'week': row['week'],
                'team': team,

                # Stats
                'cumulative_wins': cumulative_wins,
                'cumulative_games': cumulative_games,
                'year_week': f"Y{row['year']}_W{str(row['week']).zfill(2)}"
            })

    weekly_player_perf = pd.DataFrame(weekly_player_perf)
    weekly_player_perf['win_ratio'] = weekly_player_perf['cumulative_wins'] / weekly_player_perf['cumulative_games']
    weekly_player_perf['cumulative_wins'] - (weekly_player_perf['cumulative_games'] - weekly_player_perf['cumulative_wins'])
    weekly_player_perf['win_loss_diff'] = weekly_player_perf['cumulative_wins'] - (weekly_player_perf['cumulative_games'] - weekly_player_perf['cumulative_wins'])
        
    return pd.DataFrame(weekly_player_perf)


def get_owner_stats(all_matchup_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with aggregated statistics for each team in the league:
        'team': team
        'wins': sum of wins
        'losses': sum of loses
        'win_rate': wins / (wins + losses)
        'points_for': sum of points the team made
        'points_against': sum of points the other team made
        'longest_winning_streak': longest winning streak in the period
        'longest_losing_streak': longest losing streak in the period
    """
    all_time_stats = []

    teams = set(all_matchup_stats['home_team']).union(set(all_matchup_stats['away_team'].dropna()))

    for team in teams:
        team_stats = {
            'team': team,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'points_for': 0,
            'points_against': 0,
            'longest_winning_streak': 0,
            'longest_losing_streak': 0
        }

        current_winning_streak = 0
        current_losing_streak = 0

        for _, row in all_matchup_stats.iterrows():
            if row['home_team'] == team:
                team_stats['points_for'] += row['home_score']
                team_stats['points_against'] += row['away_score']
                if row['winning_team'] == team:
                    team_stats['wins'] += 1
                    current_winning_streak += 1
                    current_losing_streak = 0
                elif row['away_team'] is not None:
                    team_stats['losses'] += 1
                    current_losing_streak += 1
                    current_winning_streak = 0
            elif row['away_team'] == team:
                team_stats['points_for'] += row['away_score']
                team_stats['points_against'] += row['home_score']
                if row['winning_team'] == team:
                    team_stats['wins'] += 1
                    current_winning_streak += 1
                    current_losing_streak = 0
                else:
                    team_stats['losses'] += 1
                    current_losing_streak += 1
                    current_winning_streak = 0

            team_stats['longest_winning_streak'] = max(team_stats['longest_winning_streak'], current_winning_streak)
            team_stats['longest_losing_streak'] = max(team_stats['longest_losing_streak'], current_losing_streak)
            if (team_stats['wins'] + team_stats['losses']) > 0:
                team_stats['win_rate'] = team_stats['wins'] / (team_stats['wins'] + team_stats['losses'])
            else:
                team_stats['win_rate'] = 0

        all_time_stats.append(team_stats)

    return pd.DataFrame(all_time_stats)









