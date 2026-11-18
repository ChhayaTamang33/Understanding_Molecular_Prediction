
"""Cmd to run this script: streamlit run app.py"""

# Imports
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


## Page setup
st.set_page_config(
    page_title="Molecular Solubility Explorer",
    layout="wide"
)

st.html("""
<style>
[data-testid="stMainBlockContainer"] {
    padding-top: 2rem !important;
}
</style>
""")

st.title("Molecular Solubility Explorer")
st.caption(
    "Explore molecular properties and their relationship "
    "with measured and predicted solubility."
)


## Data loading
@st.cache_data
def load_data():
    path = Path(__file__).with_name("delaney-processed.csv")
    return pd.read_csv(path)


df = load_data()

# Clean column names in case the CSV contains extra spaces
df.columns = df.columns.str.strip()

# Convert numerical columns to numeric values
numeric_columns = [
    "ESOL predicted log solubility in mols per litre",
    "Minimum Degree",
    "Molecular Weight",
    "Number of H-Bond Donors",
    "Number of Rings",
    "Number of Rotatable Bonds",
    "Polar Surface Area",
    "measured log solubility in mols per litre"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove rows without the main values needed for visualization
df = df.dropna(
    subset=[
        "Compound ID",
        "Molecular Weight",
        "ESOL predicted log solubility in mols per litre",
        "measured log solubility in mols per litre"
    ]
)


## Column names for easier use
predicted = "ESOL predicted log solubility in mols per litre"
measured = "measured log solubility in mols per litre"
weight = "Molecular Weight"
rings = "Number of Rings"
donors = "Number of H-Bond Donors"
rotatable = "Number of Rotatable Bonds"
surface = "Polar Surface Area"


## Input widgets (on sidebar)

st.sidebar.header("Data filters")

# Filter by molecular weight
min_weight = float(df[weight].min())
max_weight = float(df[weight].max())

weight_range = st.sidebar.slider(
    "Molecular Weight",
    min_value=min_weight,
    max_value=max_weight,
    value=(min_weight, max_weight)
)

# Filter by number of rings
ring_values = sorted(df[rings].dropna().unique())

selected_rings = st.sidebar.multiselect(
    "Number of Rings",
    ring_values,
    default=ring_values
)

# Filter by number of H-bond donors
donor_values = sorted(df[donors].dropna().unique())

selected_donors = st.sidebar.multiselect(
    "Number of H-Bond Donors",
    donor_values,
    default=donor_values
)


## Data filtering

filtered = df[
    df[weight].between(weight_range[0], weight_range[1])
    & df[rings].isin(selected_rings)
    & df[donors].isin(selected_donors)
]

if filtered.empty:
    st.warning("No compounds match the selected filters.")
    st.stop()


## Overview

st.header("Overview")

st.caption(
    f"{len(filtered):,} compounds displayed"
)

# Calculate metrics
avg_weight = filtered[weight].mean()
avg_solubility = filtered[measured].mean()
avg_predicted = filtered[predicted].mean()
avg_difference = (filtered[measured] - filtered[predicted]).abs().mean()

# Display metrics
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total compounds",
    f"{len(filtered):,}"
)

col2.metric(
    "Avg. molecular weight",
    f"{avg_weight:.2f} g/mol"
)

col3.metric(
    "Avg. measured solubility",
    f"{avg_solubility:.2f}"
)

col4.metric(
    "Mean absolute prediction error",
    f"{avg_difference:.2f}"
)


## Charts

# Graph 1: Molecular Weight vs Measured Solubility
scatter_weight = px.scatter(
    filtered,
    x=weight,
    y=measured,
    color=rings,
    hover_name="Compound ID",
    hover_data=[
        predicted,
        donors,
        rotatable,
        surface
    ],
    title="Molecular Weight vs Measured Solubility",
    labels={
        weight: "Molecular Weight (g/mol)",
        measured: "Measured Log Solubility (mol/L)",
        rings: "Number of Rings"
    },
    color_continuous_scale="Viridis",
    render_mode="svg"
)


# Graph 2: Predicted vs Measured Solubility
scatter_prediction = px.scatter(
    filtered,
    x=predicted,
    y=measured,
    hover_name="Compound ID",
    hover_data=[
        weight,
        rings,
        donors,
        surface
    ],
    title="Predicted vs Measured Solubility",
    labels={
        predicted: "ESOL Predicted Log Solubility (mol/L)",
        measured: "Measured Log Solubility (mol/L)"
    },
    render_mode="svg"
)

# Add reference line (perfect prediction)
min_value = min(
    filtered[predicted].min(),
    filtered[measured].min()
)

max_value = max(
    filtered[predicted].max(),
    filtered[measured].max()
)

scatter_prediction.add_shape(
    type="line",
    x0=min_value,
    y0=min_value,
    x1=max_value,
    y1=max_value,
    line=dict(
        color="red",
        dash="dash"
    )
)


# Graph 3: Average solubility by number of rings
ring_summary = (
    filtered.groupby(rings)[measured]
    .mean()
    .reset_index(name="Average Solubility")
)

bar_chart = px.bar(
    ring_summary,
    x=rings,
    y="Average Solubility",
    title="Average Measured Solubility by Number of Rings",
    labels={
        rings: "Number of Rings",
        "Average Solubility": "Average Log Solubility (mol/L)"
    },
    color="Average Solubility",
    color_continuous_scale="Viridis"
)


## Chart layout

for chart in [
    scatter_weight,
    scatter_prediction,
    bar_chart
]:
    chart.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=80, b=40),
        legend=dict(
            orientation="h",
            y=1.12,
            x=0
        ),
        legend_title_text=""
    )


## Display charts

left, middle, right = st.columns(3)

left.plotly_chart(
    scatter_weight,
    width="stretch"
)

middle.plotly_chart(
    scatter_prediction,
    width="stretch"
)

right.plotly_chart(
    bar_chart,
    width="stretch"
)



