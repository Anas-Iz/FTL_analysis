import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import os
# === CONFIGURATION ===

datetime_column = 'date'
datetime_format = '%Y-%m-%d_%H:%M:%S'

# === LOAD DATA ===

csv_path = "allData.csv"

if not os.path.exists(csv_path):
    import requests
    url = "https://www.dropbox.com/scl/fi/27mkxgglgiod63qd2ovkb/allData.csv?rlkey=0zjhkddqnaqt5mergyjv5sh1i&st=27a3u2vr&dl=1"
    with open(csv_path, "wb") as f:
        f.write(requests.get(url).content)

df = pd.read_csv(csv_path)
df[datetime_column] = pd.to_datetime(df[datetime_column], format=datetime_format)
start_time = df[datetime_column].iloc[0]
df['elapsed_sec'] = (df[datetime_column] - start_time).dt.total_seconds()

# === UI ===
st.title("Flight Data Explorer")
st.markdown("---")

# Column selection
available_columns = [col for col in df.columns if df[col].dtype != 'object' and col != datetime_column]
columns_to_plot = st.multiselect("Select columns to plot:", available_columns)

# Normalize toggle
normalize = st.checkbox("Normalize data (0 to 1 range)", value=True)

# Time filtering
filter_option = st.radio("Filter by time:", ["No filter", "Elapsed seconds"])

if filter_option == "Elapsed seconds":
    t_min, t_max = float(df['elapsed_sec'].min()), float(df['elapsed_sec'].max())
    t_range = st.slider("Select time range (seconds):", t_min, t_max, (t_min, t_max))
    df = df[df['elapsed_sec'].between(t_range[0], t_range[1])]



# elif filter_option == "Absolute datetime":
#     import datetime
#     # Get min and max times as datetime.time
#     times = df[datetime_column].dt.time
#     min_time = min(times)
#     max_time = max(times)

#     # Split min and max time into components
#     min_h, min_m, min_s = min_time.hour, min_time.minute, min_time.second
#     max_h, max_m, max_s = max_time.hour, max_time.minute, max_time.second

#     # Input for start time components
#     start_h = st.number_input("Start hour (0-23):", min_value=0, max_value=23, value=min_h)
#     start_m = st.number_input("Start minute (0-59):", min_value=0, max_value=59, value=min_m)
#     start_s = st.number_input("Start second (0-59):", min_value=0, max_value=59, value=min_s)
#     start_time = datetime.time(hour=start_h, minute=start_m, second=start_s)

#     # Input for end time components
#     end_h = st.number_input("End hour (0-23):", min_value=0, max_value=23, value=max_h)
#     end_m = st.number_input("End minute (0-59):", min_value=0, max_value=59, value=max_m)
#     end_s = st.number_input("End second (0-59):", min_value=0, max_value=59, value=max_s)
#     end_time = datetime.time(hour=end_h, minute=end_m, second=end_s)

#     # Filter dataframe by time range
#     if start_time <= end_time:
#         df = df[df[datetime_column].dt.time.between(start_time, end_time)]
#     else:
#         df = df[(df[datetime_column].dt.time >= start_time) | (df[datetime_column].dt.time <= end_time)]





# X-axis selection
x_column = st.radio("X-axis:", ["elapsed_sec", datetime_column])

# Downsample to 0.1-second intervals
bin_size = 0.1
df['elapsed_bin'] = (df['elapsed_sec'] // bin_size).astype(int) * bin_size
df_downsampled = df.groupby('elapsed_bin').first().reset_index(drop=False)
x_plot = 'elapsed_bin' if x_column == 'elapsed_sec' else datetime_column


# === PLOTTING ===
fig = go.Figure()

if columns_to_plot:
    for col in columns_to_plot:
        y_raw = df_downsampled[col]
        y_min = y_raw.min()
        y_max = y_raw.max()

        if normalize:
            y_norm = np.zeros_like(y_raw) if y_max == y_min else (y_raw - y_min) / (y_max - y_min)
        else:
            y_norm = y_raw

        fig.add_trace(go.Scatter(
            x=df_downsampled[x_plot],
            y=y_norm,
            mode='lines+markers',
            name=col,
            customdata=np.stack((y_raw,), axis=-1),
            hovertemplate='%{x}<br>' + col + ': %{customdata[0]:.3f}<extra></extra>'
        ))

    fig.update_layout(
        title="Selected Data Over Time",
        xaxis_title=x_column,
        yaxis_title="Normalized Value (0 to 1)" if normalize else "Raw Values",
        hovermode='x unified',
        width=900,
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Select at least one column to visualize.")
