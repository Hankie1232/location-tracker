import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# --- CSV URLs instead of Google API ---
CSV_URLS = {
    "2nd": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTAu3Nv_Z7LvgPJ_YtIM14b5xrro004iNc_xjs6_Fgxn2NE_KTktnkyADzeGSgD99RYO6RKOZsYOpsN/pub?gid=1505254047&single=true&output=csv",
    "3rd": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTAu3Nv_Z7LvgPJ_YtIM14b5xrro004iNc_xjs6_Fgxn2NE_KTktnkyADzeGSgD99RYO6RKOZsYOpsN/pub?gid=2010753039&single=true&output=csv"
}

# --- Helper to load CSV ---
def load_data(sheet_name):
    url = CSV_URLS[sheet_name]
    df = pd.read_csv(url)

    # Ensure proper types
    df = df.dropna(subset=["Timestamp"])
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    df = df.dropna(subset=["X", "Y", "Timestamp"])
    df["Floor"] = sheet_name
    return df

# Background mapping
floor_bg = {"2nd": "2ndfloor.jpg", "3rd": "3rdfloor.jpg"}
bg_images = {floor: Image.open(path) for floor, path in floor_bg.items()}

try:
    # --- Load both floors ---
    df_2nd = load_data("2nd")
    df_3rd = load_data("3rd")
    df_all = pd.concat([df_2nd, df_3rd], ignore_index=True)

    # --- Latest tag position ---
    latest = df_all.sort_values("Timestamp").iloc[-1]

    st.title("🏢 Latest Tag Position")
    st.success(
        f"**{latest['Tag']}** at "
        f"X={latest['X']:.2f}, Y={latest['Y']:.2f} "
        f"on **{latest['Floor']} floor** (Timestamp: {latest['Timestamp']})"
    )

    # Background mapping
    floor_bg = {"2nd": "2ndfloor.jpg", "3rd": "3rdfloor.jpg"}
    bg_file = floor_bg.get(latest["Floor"], None)

    # Latest point chart
    fig_latest = px.scatter(
        pd.DataFrame([latest]),
        x="X",
        y="Y",
        color="Tag",
        hover_data={"Timestamp": True, "X": True, "Y": True, "Floor": True},
    )
    if bg_file:
        fig_latest.update_layout(
            images=[
                dict(
                    source=bg_images[latest["Floor"]],
                    xref="x",
                    yref="y",
                    x=-10,
                    y=50,
                    sizex=50,
                    sizey=50,
                    sizing="stretch",
                    opacity=0.5,
                    layer="below",
                )
            ]
        )

    fig_latest.update_traces(marker=dict(size=20, line=dict(width=2, color="black")))
    fig_latest.update_layout(
        width=600,
        height=600,
        title="Latest Tag Position",
        xaxis=dict(range=[-10, 40]),
        yaxis=dict(range=[0, 55]),
    )

    st.plotly_chart(fig_latest, use_container_width=True)

    st.divider()

    # --- Floor tag viewer ---
    st.header("📊 Floor Tag Viewer")
    floor_choice = st.radio("Select Floor:", ["2nd", "3rd"])
    df = load_data(floor_choice)

    tag_options = ["All"] + sorted(df["Tag"].unique().tolist())
    tag_choice = st.selectbox("Select Tag:", tag_options, index=0)

    limit_options = [50, 100, 250, "All"]
    limit_choice = st.selectbox("How many latest positions?", limit_options, index=3)

    # Filtering
    if tag_choice != "All":
        df_filtered = df[df["Tag"] == tag_choice].sort_values("Timestamp")
        if limit_choice != "All":
            df_filtered = df_filtered.tail(limit_choice)
    else:
        frames = []
        for tag in df["Tag"].unique():
            tag_df = df[df["Tag"] == tag].sort_values("Timestamp")
            if limit_choice != "All":
                tag_df = tag_df.tail(limit_choice)
            frames.append(tag_df)
        df_filtered = pd.concat(frames, ignore_index=True)

    # --- Fade effect ---
    df_filtered = df_filtered.sort_values("Timestamp")
    df_filtered["order"] = df_filtered.groupby("Tag").cumcount()
    df_filtered["alpha"] = df_filtered.groupby("Tag")["order"].rank(pct=True)

    tag_colors = {"Tag1": "blue", "Tag2": "red"}

    fig = px.scatter(
        df_filtered,
        x="X",
        y="Y",
        color="Tag",
        hover_data={"Timestamp": True, "X": True, "Y": True},
        opacity=df_filtered["alpha"],
        color_discrete_map=tag_colors,
    )

    bg_file = floor_bg.get(floor_choice, None)
    if bg_file:
        fig.update_layout(
            images=[
                dict(
                    source=bg_images[floor_choice],
                    xref="x",
                    yref="y",
                    x=-10,
                    y=50,
                    sizex=50,
                    sizey=50,
                    sizing="stretch",
                    opacity=0.5,
                    layer="below",
                )
            ]
        )

    fig.update_traces(marker=dict(size=10))
    fig.update_layout(
        width=600,
        height=600,
        title=f"{floor_choice} Floor - {tag_choice} (Last {limit_choice} positions)"
        if limit_choice != "All"
        else f"{floor_choice} Floor - {tag_choice} (All positions)",
        xaxis=dict(range=[-10, 40]),
        yaxis=dict(range=[0, 55]),
    )

    st.plotly_chart(fig, use_container_width=True)

    # 🔽 Sort descending before showing the table
    df_filtered = df_filtered.sort_values("Timestamp", ascending=False)
    st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Error: {e}")
