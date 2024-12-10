import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch, FontManager
import streamlit as st
import os
import io

# App configuration
st.set_page_config(page_title="ShotMap Dashboard", layout="wide")

# FontManager for custom font
fm_rubik = FontManager('https://raw.githubusercontent.com/google/fonts/main/ofl/rubikmonoone/RubikMonoOne-Regular.ttf')

# Define the pitch
pitch = VerticalPitch(
    pad_bottom=0.5, half=True, pitch_type='opta', goal_type='box',
    goal_alpha=0.8, pitch_color='grass', line_color='white', stripe=True
)

# Function to plot the shotmap
def plot_shot_map(df, team_name, player_name=None, highlight_rows=None):
    # Filter the relevant shots for the team
    team_shots = df[
        (df['isHome'] & (df['home_team'] == team_name)) | 
        (~df['isHome'] & (df['away_team'] == team_name))
    ].copy()

    # Further filter by player if specified
    if player_name:
        team_shots = team_shots[team_shots['name'] == player_name]

    # Separate goals and non-goal shots
    df_goals = team_shots[team_shots['shotType'] == 'goal']
    df_non_goal_shots = team_shots[team_shots['shotType'] != 'goal']

    # Create the pitch plot
    fig, ax = pitch.draw(figsize=(12, 10))

    # Plot non-goal shots
    pitch.scatter(
        100 - df_non_goal_shots['x'], 100 - df_non_goal_shots['y'],
        s=750, edgecolors='black', c='white', marker='o', ax=ax
    )

    # Plot goal shots
    pitch.scatter(
        100 - df_goals['x'], 100 - df_goals['y'],
        s=750, edgecolors='black', linewidths=0.6, c='white', marker='football', ax=ax
    )

    # Highlight selected rows
    if highlight_rows is not None:
        for _, row in highlight_rows.iterrows():
            pitch.scatter(
                [100 - row['x']],
                [100 - row['y']],
                s=1200, edgecolors='gold', c='red', marker='*', ax=ax, label="Selected Shot"
            )

    # Add title
    title = f"{team_name} ShotMap"
    if player_name:
        title += f" - {player_name}"
    ax.set_title(title, size=20, fontproperties=fm_rubik.prop, pad=20)
    
    return fig, team_shots  # Return the filtered DataFrame for display

# Path to the CSV file
file_path = "aggregated_shotmap_data.csv"

# Check if the file exists
if os.path.exists(file_path):
    # Load the data
    df = pd.read_csv(file_path)

    # Sidebar for filtering options
    st.sidebar.header("Filter Options")

    # Extract unique team names
    unique_teams = sorted(pd.concat([df['home_team'], df['away_team']]).unique())

    # Dropdown for team selection
    selected_team = st.sidebar.selectbox("Select a Team", unique_teams)

    # Filter players based on the selected team
    team_players = df[
        ((df['isHome'] & (df['home_team'] == selected_team)) | 
         (~df['isHome'] & (df['away_team'] == selected_team)))
    ]['name'].dropna().unique()
    
    # Dropdown for player selection
    selected_player = st.sidebar.selectbox("Select a Player", ["All Players"] + sorted(team_players))

    # Filter by `shotType`
    shot_types = df['shotType'].dropna().unique()
    selected_shot_types = st.sidebar.multiselect("Select Shot Types", shot_types, default=shot_types)

    # Filter by player and `shotType`
    player_filter = None if selected_player == "All Players" else selected_player
    filtered_df = df[df['shotType'].isin(selected_shot_types)]

    # Generate the shotmap plot
    if selected_team:
        fig, team_shots = plot_shot_map(filtered_df, selected_team, player_filter)
        st.pyplot(fig)

        # Display the final filtered DataFrame
        st.subheader(f"Data for {selected_team}")
        if player_filter:
            st.subheader(f"Filtered by Player: {selected_player}")

        # Calculate dynamic DataFrame height
        num_rows = len(team_shots)
        row_height = 35  # Approximate height per row in pixels
        min_height = row_height * 3
        dataframe_height = min_height if num_rows <= 3 else row_height * num_rows

        # Display DataFrame with dynamic height
        st.dataframe(team_shots, height=dataframe_height)

        # Add row selection
        selected_indices = st.multiselect("Select Rows to Highlight", team_shots.index.tolist())
        highlighted_rows = team_shots.loc[selected_indices]

        # Highlight the selected rows in the shotmap
        if not highlighted_rows.empty:
            fig, _ = plot_shot_map(filtered_df, selected_team, player_filter, highlight_rows=highlighted_rows)
            st.pyplot(fig)

        # Option to download the plot
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        st.download_button(
            label="Download ShotMap",
            data=buf,
            file_name=f"{selected_team}_ShotMap.png",
            mime="image/png"
        )
else:
    st.error(f"The file {file_path} does not exist. Please ensure it is in the same directory as this script.")
