from typing import List
import pandas as pd
import altair as alt

# Create a line chart of the cumulative_wins column of weekly_owner_stats over each year_week, each team should have their own line
def team_filter(input_data, selected_teams):
    return input_data[[team for team in input_data.columns if team in selected_teams]]


def cumulative_wins_chart(weekly_owner_stats: pd.DataFrame, selected_teams: List[str]) -> None:
    # Create a line chart of the cumulative_wins column of weekly_owner_stats over each year_week, each team should have their own line
    cumulative_wins_chart_data = weekly_owner_stats.pivot(index='year_week', columns='team', values='cumulative_wins')
    cumulative_wins_chart_data = team_filter(cumulative_wins_chart_data, selected_teams)
    cumulative_wins_chart_data = cumulative_wins_chart_data.reset_index().melt(id_vars=['year_week'], var_name='team', value_name='cumulative_wins')
    
    # Create a selection object for hover
    hover = alt.selection_point(
        fields=["year_week"],
        nearest=True,
        on="pointerover",
        empty=False,
        clear="pointerout",
    )

    # Base chart
    base = alt.Chart(cumulative_wins_chart_data).encode(
        x='year_week:O'
    )

    # Lines
    lines = base.mark_line().encode(
        y='cumulative_wins:Q',
        color='team:N'
    )

    # Points
    points = lines.mark_point().transform_filter(hover)

    # Rule for tooltips
    tooltips = [alt.Tooltip("year_week", title="Week")] + [alt.Tooltip(c, type='quantitative') for c in cumulative_wins_chart_data['team'].unique()]
    rule = base.transform_pivot(
        'team', value='cumulative_wins', groupby=['year_week']
    ).mark_rule().encode(
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=tooltips
    ).add_params(hover)

    # Combine lines, points, and rule
    chart = lines + points + rule

    # Set chart properties
    chart = chart.properties(
        width=800,
        height=600
    ).interactive()

    return chart


def weekly_wins_minus_losses_chart(weekly_owner_stats, selected_teams):
    win_loss_diff_chart_data = weekly_owner_stats.pivot(index='year_week', columns='team', values='win_loss_diff')
    win_loss_diff_chart_data = team_filter(win_loss_diff_chart_data, selected_teams)
    win_loss_diff_chart_data = win_loss_diff_chart_data.reset_index().melt(id_vars=['year_week'], var_name='team', value_name='win_loss_diff')
    print(win_loss_diff_chart_data.columns)

    # Create a selection object for hover
    hover = alt.selection_point(
        fields=["year_week"],
        nearest=True,
        on="pointerover",
        empty=False,
        clear="pointerout",
    )

    # Base chart
    base = alt.Chart(win_loss_diff_chart_data).encode(
        x='year_week:O'
    )

    # Lines
    lines = base.mark_line().encode(
        y='win_loss_diff:Q',
        color='team:N'
    )

    # Points
    points = lines.mark_point().transform_filter(hover)

    # Rule for tooltips
    tooltips = [alt.Tooltip("year_week", title="Week")] + [alt.Tooltip(c, type='quantitative') for c in win_loss_diff_chart_data['team'].unique()]
    rule = base.transform_pivot(
        'team', value='win_loss_diff', groupby=['year_week']
    ).mark_rule().encode(
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=tooltips
    ).add_params(hover)

    # Combine lines, points, and rule
    chart = lines + points + rule

    # Set chart properties
    chart = chart.properties(
        width=800,
        height=600
    ).interactive()

    return chart


def matchup_scatterplot(weekly_matchups, selected_teams, playoff_selection="All Matchups"):
    """
    Create an altair scatterplot of the home_score vs away_score for each matchup, with the color of the points indicated by the winning team.
    The tooltip should include: year, week, winning team, losing team, winning_score, losing_score, is_playoff
    """
    filtered_data = weekly_matchups[
        (weekly_matchups['home_team'].isin(selected_teams)) | 
        (weekly_matchups['away_team'].isin(selected_teams))
    ]
    
    if playoff_selection == 'Playoffs':
        filtered_data = filtered_data[filtered_data['is_playoff']]
    elif playoff_selection == 'Regular Season':
        filtered_data = filtered_data[~filtered_data['is_playoff']]
    else:
        pass

    scatter = alt.Chart(filtered_data).mark_circle(size=100).encode(
        x='losing_score:Q',
        y='winning_score:Q',
        color='winning_team:N',
        tooltip=[
            alt.Tooltip('year', title='Year'),
            alt.Tooltip('week', title='Week'),
            alt.Tooltip('winning_team', title='Winning Team'),
            alt.Tooltip('winning_score', title='Winning Score'),
            alt.Tooltip('losing_team', title='Losing Team'),
            alt.Tooltip('losing_score', title='Losing Score'),
            alt.Tooltip('is_playoff', title='Playoff Game')
        ]
    ).properties(
        width=800,
        height=600
    ).interactive()

    return scatter


def beat_percent_box(weekly_matchups, selected_teams):
    """
    Create a box plot of the beat percent for each team. The color should be based on the percentage. 
    """
    def get_beat_stats(weekly_matchups):
        beat_stats = []

        teams = weekly_matchups['home_team'].unique()

        for team in teams:
            for beat_team in teams:  # Compare each team to every other team
                if team != beat_team:
                    matchups = weekly_matchups[((weekly_matchups['home_team'] == team) & (weekly_matchups['away_team'] == beat_team)) |
                                                    ((weekly_matchups['away_team'] == team) & (weekly_matchups['home_team'] == beat_team))]
                    beat_count = matchups[matchups['winning_team'] == team].shape[0]
                    total_matchups = matchups.shape[0]
                    beat_pct = beat_count / total_matchups if total_matchups > 0 else 0
                    beat_diff_p50 = matchups[matchups['winning_team'] == team]['score_diff'].median() if beat_count > 0 else 0
                    beat_diff_p75 = matchups[matchups['winning_team'] == team]['score_diff'].quantile(0.75) if beat_count > 0 else 0
                    beat_diff_p90 = matchups[matchups['winning_team'] == team]['score_diff'].quantile(0.90) if beat_count > 0 else 0

                    beat_stats.append({
                        'team': team,
                        'beat_team': beat_team,
                        'matchup_count': total_matchups,
                        'beat_count': beat_count,
                        'beat_pct': beat_pct,
                        'beat_diff_p50': beat_diff_p50,
                        'beat_diff_p75': beat_diff_p75,
                        'beat_diff_p90': beat_diff_p90
                    })

        return pd.DataFrame(beat_stats)

    beat_stats = get_beat_stats(weekly_matchups)
    # TODO: filter beat_stats to only include selected_teams
    beat_stats = beat_stats[
        (beat_stats['team'].isin(selected_teams)) 
    #    & (beat_stats['beat_team'].isin(selected_teams))
    ]

    
    box_plot = alt.Chart(beat_stats).mark_rect().encode(
        x=alt.X('beat_team:N', title='... beat this team'),
        y=alt.Y('team:N', title='This team...'),
        color=alt.Color('beat_pct:Q', title='Beat Percentage', scale=alt.Scale(scheme='viridis')),
        tooltip=[
            alt.Tooltip('team:N', title='Team'),
            alt.Tooltip('beat_team:N', title='Beat Team'),
            alt.Tooltip('matchup_count:Q', title='Matchup Count'),
            alt.Tooltip('beat_count:Q', title='Beat Count'),
            alt.Tooltip('beat_pct:Q', title='Beat Percentage', format='.2%'),
            alt.Tooltip('beat_diff_p50:Q', title='Beat Diff P50'),
            alt.Tooltip('beat_diff_p75:Q', title='Beat Diff P75'),
            alt.Tooltip('beat_diff_p90:Q', title='Beat Diff P90')
        ]
    ).properties(
        width=800,
        height=600
    ).interactive()

    text = box_plot.mark_text(baseline='middle').encode(
        alt.Text('beat_pct:Q', format=".2f"),
        color=alt.condition(
            alt.datum.beat_pct > 0.50,
            alt.value('black'),
            alt.value('white')
        )
    )
    # text = box_plot.mark_text(align='center', baseline='middle', color='red').encode(
    #     text=alt.Text('beat_pct:Q', format='.2%')
    # )

    box_plot = box_plot + text

    return box_plot
