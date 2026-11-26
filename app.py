from pathlib import Path
import sqlite3
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from vo2max import rockport_vo2max

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "vo2max_ai.sqlite3"

st.set_page_config(
    page_title="VO2MAX AI",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #f5f7fb; }
    .block-container { max-width: 1220px; padding-top: 1.8rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { background: #101d35; }
    [data-testid="stSidebar"] * { color: #f5f7fb !important; }
    .hero {
        background: linear-gradient(120deg, #10213d 0%, #173d55 60%, #176b5b 100%);
        padding: 1.7rem 1.9rem; border-radius: 20px; color: white;
        margin-bottom: 1.25rem;
    }
    .hero h1 { color: white; margin: 0 0 .35rem 0; font-size: 2.25rem; }
    .hero p { color: #d9e8ef; margin: 0; font-size: 1rem; }
    .subtle { color: #617086; font-size: .92rem; }
    .info-card {
        background: white; border: 1px solid #e6ebf2; border-radius: 16px;
        padding: 1rem 1.15rem; min-height: 105px;
    }
    .info-card .label { color: #64748b; font-size: .85rem; }
    .info-card .value { color: #10213d; font-size: 1.75rem; font-weight: 750; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e6ebf2; border-radius: 14px;
        padding: 14px 16px;
    }
    .stButton button[kind="primary"] {
        background: #087f68; border: 0; border-radius: 10px; font-weight: 650;
    }
    .stButton button[kind="primary"]:hover { background: #066b58; }
    .small-note { color: #64748b; font-size: .82rem; }
</style>
""", unsafe_allow_html=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_name TEXT NOT NULL,
                assessment_date TEXT NOT NULL,
                method TEXT NOT NULL,
                result_type TEXT NOT NULL,
                vo2max REAL NOT NULL,
                age INTEGER,
                equation_sex TEXT,
                weight_kg REAL,
                walk_minutes REAL,
                finishing_hr REAL,
                source TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_assessment(record):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO assessments (
                participant_name, assessment_date, method, result_type, vo2max,
                age, equation_sex, weight_kg, walk_minutes, finishing_hr,
                source, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["participant_name"], record["assessment_date"], record["method"],
            record["result_type"], record["vo2max"], record.get("age"),
            record.get("equation_sex"), record.get("weight_kg"),
            record.get("walk_minutes"), record.get("finishing_hr"),
            record.get("source"), record.get("notes"),
            datetime.now().isoformat(timespec="seconds"),
        ))
        conn.commit()


def load_assessments():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM assessments ORDER BY assessment_date DESC, id DESC",
            conn
        )


def show_hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


init_db()

with st.sidebar:
    st.markdown("## 🫀 VO2MAX AI")
    st.caption("Cardiovascular fitness insights")
    page = st.radio(
        "Navigation",
        ["Overview", "New assessment", "Assessment history", "Methodology"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Version 1.0 · Local MVP")
    st.caption("Your records are stored in a local SQLite database on this computer.")

df = load_assessments()

if page == "Overview":
    show_hero("Understand your fitness.", "A simple place to record, understand and track cardiovascular fitness measurements.")
    if df.empty:
        st.info("Welcome! You haven't saved an assessment yet. Start with a Rockport 1-mile walk estimate or add a laboratory CPET measurement.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏃 Field-test estimate")
            st.write("Use the Rockport 1-mile walk protocol to calculate an equation-based estimate.")
        with c2:
            st.markdown("### 🧪 Laboratory measurement")
            st.write("Record a VO₂ max value measured during a supervised CPET test.")
            st.write("The app keeps measured and estimated values clearly separated.")
        st.info("To begin, choose **New assessment** from the navigation menu in the left sidebar.")
    else:
        latest = df.iloc[0]
        total = len(df)
        latest_label = f'{latest["vo2max"]:.1f}'
        measured_count = int((df["result_type"] == "Measured").sum())
        estimated_count = int((df["result_type"] == "Estimated").sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latest VO₂ max", f'{latest_label} mL/kg/min')
        c2.metric("Assessments", total)
        c3.metric("Measured CPET", measured_count)
        c4.metric("Field estimates", estimated_count)

        st.markdown("### Your assessment history")
        chart_df = df.copy()
        chart_df["assessment_date"] = pd.to_datetime(chart_df["assessment_date"])
        chart_df = chart_df.sort_values("assessment_date")
        fig = px.line(
            chart_df, x="assessment_date", y="vo2max", color="method",
            markers=True, hover_data=["participant_name", "result_type"],
            labels={
                "assessment_date": "Assessment date",
                "vo2max": "VO₂ max (mL/kg/min)",
                "method": "Method",
            },
        )
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=10, r=10, t=20, b=10),
            legend_title_text="Assessment method",
        )
        fig.update_yaxes(rangemode="tozero", gridcolor="#edf1f5")
        fig.update_xaxes(gridcolor="#edf1f5")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Recent assessments")
        display_cols = ["assessment_date", "participant_name", "method", "result_type", "vo2max"]
        recent = df[display_cols].head(5).copy()
        recent.columns = ["Date", "Name", "Method", "Result type", "VO₂ max (mL/kg/min)"]
        st.dataframe(recent, use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Important: VO₂ max is one measure of cardiorespiratory fitness. An estimate is not the same as a laboratory measurement.")

elif page == "New assessment":
    show_hero("New assessment", "Choose the method that matches the information you actually have.")
    st.warning("Exercise testing can carry risk. Do not perform a maximal or brisk exercise test if you have symptoms, an acute illness, or have been advised to avoid exercise. Seek qualified medical guidance when unsure.")

    method = st.radio(
        "Assessment method",
        ["Rockport 1-mile walk (estimated)", "Laboratory CPET (measured)"],
        horizontal=True,
    )
    st.divider()

    if method.startswith("Rockport"):
        st.markdown("### 🏃 Rockport 1-mile walk")
        st.write("This equation estimates VO₂ max from a standardized one-mile walk. Walk as fast as you safely can without running, on a flat measured course. Record the total time and heart rate immediately at the finish.")
        with st.expander("Before you begin — test protocol", expanded=False):
            st.markdown("""
            1. Use a flat, accurately measured 1-mile (1.609 km) course.
            2. Warm up gently and follow a consistent protocol.
            3. Walk briskly; do not jog or run.
            4. Record total time in minutes and seconds.
            5. Measure finishing heart rate immediately after completing the mile.
            6. Stop if you develop chest discomfort, unusual breathlessness, dizziness or feel unwell.
            """)
        with st.form("rockport_form"):
            a, b = st.columns(2)
            with a:
                participant = st.text_input("Name or participant ID", placeholder="e.g. Runner 001")
                test_date = st.date_input("Assessment date", value=date.today())
                age = st.number_input("Age (years)", min_value=30, max_value=69, value=35, step=1)
                sex_label = st.selectbox(
                    "Equation sex category",
                    ["Male (original equation coding)", "Female (original equation coding)", "Not applicable / prefer not to say"],
                )
            with b:
                weight = st.number_input("Body weight (kg)", min_value=35.0, max_value=200.0, value=70.0, step=0.1)
                t1, t2 = st.columns(2)
                with t1:
                    walk_min = st.number_input("Walk time — minutes", min_value=10, max_value=29, value=15, step=1)
                with t2:
                    walk_sec = st.number_input("Walk time — seconds", min_value=0, max_value=59, value=0, step=1)
                finishing_hr = st.number_input("Finishing heart rate (bpm)", min_value=60, max_value=220, value=140, step=1)
            notes = st.text_area("Notes (optional)", placeholder="Course, device used, conditions, or other context.")
            submitted = st.form_submit_button("Calculate and save estimate", type="primary", use_container_width=True)

        if submitted:
            if not participant.strip():
                st.error("Please enter a name or participant ID.")
            elif sex_label.startswith("Not applicable"):
                st.error("This published equation uses its original male/female coding. It is not appropriate to guess or extrapolate for this entry. Record a laboratory CPET measurement or use a separately validated method.")
            else:
                try:
                    equation_sex = "male" if sex_label.startswith("Male") else "female"
                    total_time = float(walk_min) + float(walk_sec) / 60.0
                    estimate = rockport_vo2max(
                        int(age), equation_sex, float(weight), total_time, float(finishing_hr)
                    )
                    save_assessment({
                        "participant_name": participant.strip(),
                        "assessment_date": test_date.isoformat(),
                        "method": "Rockport 1-mile walk",
                        "result_type": "Estimated",
                        "vo2max": estimate,
                        "age": int(age),
                        "equation_sex": equation_sex,
                        "weight_kg": float(weight),
                        "walk_minutes": total_time,
                        "finishing_hr": float(finishing_hr),
                        "source": "Rockport field-test equation",
                        "notes": notes.strip(),
                    })
                    st.success("Assessment saved successfully.")
                    st.metric("Estimated VO₂ max", f"{estimate:.1f} mL/kg/min")
                    st.caption("This is an equation-based field-test estimate, not a direct CPET measurement or a diagnosis.")
                except ValueError as exc:
                    st.error(str(exc))

    else:
        st.markdown("### 🧪 Laboratory CPET measurement")
        st.write("Use this option only for a value measured during a laboratory cardiopulmonary exercise test (CPET). Do not enter a smartwatch estimate here.")
        with st.form("cpet_form"):
            participant = st.text_input("Name or participant ID", placeholder="e.g. Runner 001")
            test_date = st.date_input("Assessment date", value=date.today(), key="cpet_date")
            measured_value = st.number_input(
                "Measured VO₂ max (mL/kg/min)", min_value=5.0, max_value=100.0,
                value=35.0, step=0.1
            )
            source = st.text_input("Laboratory / provider (optional)")
            notes = st.text_area("Notes (optional)", placeholder="Protocol, equipment, report reference, etc.")
            submitted = st.form_submit_button("Save measured result", type="primary", use_container_width=True)
        if submitted:
            if not participant.strip():
                st.error("Please enter a name or participant ID.")
            else:
                save_assessment({
                    "participant_name": participant.strip(),
                    "assessment_date": test_date.isoformat(),
                    "method": "Laboratory CPET",
                    "result_type": "Measured",
                    "vo2max": float(measured_value),
                    "source": source.strip(),
                    "notes": notes.strip(),
                })
                st.success("Laboratory measurement saved.")
                st.metric("Measured VO₂ max", f"{measured_value:.1f} mL/kg/min")

elif page == "Assessment history":
    show_hero("Assessment history", "Review saved measurements and export your records.")
    if df.empty:
        st.info("No assessments have been saved yet.")
    else:
        query = st.text_input("Filter by name or participant ID")
        filtered = df.copy()
        if query.strip():
            filtered = filtered[filtered["participant_name"].str.contains(query.strip(), case=False, na=False)]
        view = filtered[[
            "id", "assessment_date", "participant_name", "method",
            "result_type", "vo2max", "source", "notes"
        ]].copy()
        view.columns = [
            "ID", "Date", "Name / ID", "Method", "Type",
            "VO₂ max (mL/kg/min)", "Source", "Notes"
        ]
        st.dataframe(view, use_container_width=True, hide_index=True)
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download filtered records (CSV)",
            data=csv,
            file_name="vo2max_assessments.csv",
            mime="text/csv",
            type="primary",
        )
        st.caption("Records are stored locally in data/vo2max_ai.sqlite3. Keep backups of this file.")

elif page == "Methodology":
    show_hero("Methodology & limitations", "Understand what the software calculates — and what it does not.")
    st.markdown("### Rockport 1-mile walk equation")
    st.latex(r"VO_2max = 132.853 - 0.0769W - 0.3877A + 6.315S - 3.2649T - 0.1565H")
    st.markdown("""
    Where:
    - **W** = body weight in pounds
    - **A** = age in years
    - **S** = original equation coding (male = 1, female = 0)
    - **T** = one-mile walk time in minutes
    - **H** = finishing heart rate in beats per minute

    The app accepts body weight in kilograms and converts it to pounds internally.
    """)
    st.info("The Rockport result is an equation-based estimate. It is not a direct oxygen-consumption measurement and is not suitable for every population. This MVP restricts the equation to ages 30–69 and does not extrapolate for unsupported equation categories.")
    st.markdown("### Laboratory CPET")
    st.write("CPET measures respiratory gas exchange during exercise. A value entered in the CPET section is stored as a measured result supplied by the user; this application does not independently verify the laboratory report.")
    st.markdown("### Machine learning status")
    st.warning("The ML prediction feature is not enabled in Version 1.0. No validated training dataset has been supplied. The app does not fabricate predictions or train on synthetic data.")
    st.markdown("### Safety and intended use")
    st.write("This software is an educational fitness-recording tool. It does not diagnose, screen for, or treat cardiovascular or pulmonary disease. Do not undertake exercise testing if you have concerning symptoms or have been advised not to exercise. Seek qualified medical guidance when appropriate.")
    st.markdown("### Privacy")
    st.write("This local MVP stores records in a SQLite database on the computer running the app. It has no user authentication or cloud security layer. Do not expose it publicly or enter identifiable health information until authentication, access controls, encryption, backups and privacy requirements have been implemented.")
    st.markdown("### Planned next steps")
    st.write("1. Add authenticated user accounts and secure cloud storage. 2. Source a documented CPET-labelled dataset. 3. Build participant-level ML training and external validation. 4. Add model cards, uncertainty estimates and monitoring. 5. Integrate wearables only with user consent.")
