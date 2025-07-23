import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# === CONFIGURATION ===
csv_path = 'allData.csv'  # Make sure this file is in the same directory

datetime_column = 'date'
datetime_format = '%Y-%m-%d_%H:%M:%S'

# === LOAD DATA ===
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
filter_option = st.radio("Filter by time:", ["No filter", "Elapsed seconds", "Absolute datetime"])

if filter_option == "Elapsed seconds":
    t_min, t_max = float(df['elapsed_sec'].min()), float(df['elapsed_sec'].max())
    t_range = st.slider("Select time range (seconds):", t_min, t_max, (t_min, t_max))
    df = df[df['elapsed_sec'].between(t_range[0], t_range[1])]

elif filter_option == "Absolute datetime":
    dt_min, dt_max = df[datetime_column].min(), df[datetime_column].max()
    dt_range = st.slider("Select datetime range:", dt_min, dt_max, (dt_min, dt_max))
    df = df[df[datetime_column].between(dt_range[0], dt_range[1])]

# X-axis selection
x_column = st.radio("X-axis:", ["elapsed_sec", datetime_column])

grouping_series = df['elapsed_sec'].astype(int).rename('elapsed_sec_int')
df_downsampled = df.groupby(grouping_series).first().reset_index(drop=False)
x_plot = 'elapsed_sec_int' if x_column == 'elapsed_sec' else datetime_column

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
