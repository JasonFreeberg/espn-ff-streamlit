import streamlit as st
import pandas as pd
from data_methods import get_all_matchup_stats, get_owner_stats, get_weekly_owner_stats
from chart_methods import cumulative_wins_chart, weekly_wins_minus_losses_chart, matchup_scatterplot, beat_percent_box
from espn_api.football import League
import altair as alt
import os
import dotenv

dotenv.load_dotenv()

st.set_page_config(layout="wide")

# Initialize session state variables if they don't exist
if 'ESPN_S2' not in st.session_state:
    st.session_state.ESPN_S2 = None
if 'ESPN_SWID' not in st.session_state:
    st.session_state.ESPN_SWID = None
if 'ESPN_LEAGUE_ID' not in st.session_state:
    st.session_state.ESPN_LEAGUE_ID = None
if 'FIRST_YEAR' not in st.session_state:
    st.session_state.FIRST_YEAR = 2017

    # TODO: Couldn't figure out the settings tab and updating the main page here. So I just hardcoded the values for now.
    # if st.session_state.ESPN_S2 is None or st.session_state.ESPN_SWID is None or st.session_state.ESPN_LEAGUE_ID is None:
    #     st.write("Please configure your settings in the Settings tab.")
    # else:


# TODO: Put error handling here, tell user there was a problem with their settings
ALL_MATCHUP_STATS = get_all_matchup_stats(
    ESPN_S2=os.environ.get('ESPN_S2'),
    ESPN_SWID=os.environ.get('ESPN_SWID'), 
    ESPN_LEAGUE_ID=os.environ.get('ESPN_LEAGUE_ID'), 
    starting_year=2017)

# Initialize the Streamlit app with two tabs: Home and Settings
league_history, owner_analysis, settings = st.tabs(["League History", "Owner Analysis", "Settings"], )

with league_history:
    st.header("Home")

    unique_teams = pd.concat([ALL_MATCHUP_STATS['home_team'], ALL_MATCHUP_STATS['away_team']]).unique()  # TODO: Sort these by the number of seasons they've been in the league
    starting_teams = [team for team in unique_teams if team is not None]
    selected_teams = st.multiselect("Select teams to include", unique_teams, default=starting_teams)

    unique_year_weeks = ALL_MATCHUP_STATS[['year_week']].drop_duplicates()
    starting_year_weeks = (unique_year_weeks.min()[0], unique_year_weeks.max()[0])
    selected_max_min_year_weeks = st.select_slider("Select weeks to include", unique_year_weeks, value=starting_year_weeks)
    selected_year_weeks = unique_year_weeks[
        (unique_year_weeks['year_week'] >= selected_max_min_year_weeks[0]) &
        (unique_year_weeks['year_week'] <= selected_max_min_year_weeks[1])
    ]['year_week'].tolist()

    # Filter data based on user input
    filtered_all_matchup_stats = ALL_MATCHUP_STATS[(ALL_MATCHUP_STATS['year_week'].isin(selected_year_weeks))]
    owner_stats = get_owner_stats(filtered_all_matchup_stats)
    weely_owner_stats = get_weekly_owner_stats(filtered_all_matchup_stats)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(height=600):
            st.write('Records')
            st.dataframe(owner_stats)

        with st.container(height=700):
            st.write('Weekly Cumulative Wins')
            st.altair_chart(cumulative_wins_chart(weely_owner_stats, selected_teams), use_container_width=True)
        
        with st.container(height=700):
            st.write('Weekly Wins minus Losses')
            st.altair_chart(weekly_wins_minus_losses_chart(weely_owner_stats, selected_teams), use_container_width=True)
    
    with col2:
        with st.container(height=700):
            playoff_selection = st.segmented_control(
                "Matchups",
                options=['All Matchups', 'Playoffs', 'Regular Season'],
                selection_mode="single",
                default='All Matchups'
            )
            st.altair_chart(matchup_scatterplot(filtered_all_matchup_stats, selected_teams, playoff_selection), use_container_width=True)

        with st.container(height=700):
            st.write('Beat Percentages')
            st.altair_chart(beat_percent_box(filtered_all_matchup_stats, selected_teams), use_container_width=True)

with owner_analysis:
    st.header("Owner Analysis")
    st.write("Owner Analysis here")
    owner_stats = get_owner_stats(ALL_MATCHUP_STATS)
    weekly_owner_stats = get_weekly_owner_stats(ALL_MATCHUP_STATS)

    selected_owner = st.selectbox("Select an owner", owner_stats['team'].unique())

    st.dataframe(ALL_MATCHUP_STATS)
    st.dataframe(owner_stats)
    st.dataframe(weekly_owner_stats)

    games_played = weekly_owner_stats[weekly_owner_stats['team'] == selected_owner].groupby('team').size().reset_index(name='games_played')
    wins = weekly_owner_stats[(weekly_owner_stats['winning_team'] == weekly_owner_stats['team']) & (weekly_owner_stats['team'] == selected_owner)].groupby('team').size().reset_index(name='wins')
    first_year = ALL_MATCHUP_STATS['year'].min()

    intro = f"{selected_owner} has been in the league since {first_year}, played {games_played['games_played'].values[0]} games in that time and has won {wins['wins'].values[0]} of those."
    """
    What does an owner want to know?
    - How good they are
        - Lead in with history (years and games played)
        - Win percentage
        - Standings over past years
            - Their best season
                - Points, record, final standing

            - Playoff appearances
        - How they've done against other teams
            - Table with columns: Opposing Team, Wins, Games, cloest win, biggest win
        - Past rosters by year

    - Their best winning streak
        - Who they beat
    - Best come back within a season
        - Their low spot, and their high spot
    """
    


    """
    On the flip side, these are the things an owner doesn't want to know: 
    - How bad they are
    - How many times they've been blown out
    - How many times they've been beaten by the same team



    He has been blown out in these games:
        <table>
    """

with settings:
    ...
    # st.header("Settings")
    # st.write("Configure your settings here.")
    # # Add input fields for ESPN_S2, ESPN_SWID, and ESPN_LEAGUE_ID
    # st.session_state.ESPN_S2 = st.text_input("ESPN S2", value=st.session_state.ESPN_S2)
    # st.session_state.ESPN_SWID = st.text_input("ESPN SWID", value=st.session_state.ESPN_SWID)
    # st.session_state.ESPN_LEAGUE_ID = st.text_input("ESPN League ID", value=st.session_state.ESPN_LEAGUE_ID)

    # st.button("Save Settings", on_click=lambda: st.rerun())

"""
------------------------------------------------------------------------------
Need inputs for the following:
- ESPN_S2, ESPN_SWID, ESPN_LEAGUE_ID
    https://docs.streamlit.io/develop/api-reference/widgets/st.text_input 
- Teams to include
    https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect
- Weeks to include
    https://docs.streamlit.io/develop/api-reference/widgets/st.select_slider

Data flow
- 2 primary datasets, all teams and weeks (limit querying from ESPN)
    - all_time_matchup_stats
    - get the teams and weeks, will need these for the inputs and should be "global"
    
- That output is filtered by the user inputs above
    - This is the dataset that's used for the visualizations

- Other handlers:
    - get_all_time_weekly_win_records
    - get_all_time_weekly_wins_minus_losses
    - get_beat_stats
"""
