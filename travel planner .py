"""Travel Planner - a simple Streamlit app.

Run:
    pip install streamlit
    streamlit run travel_planner.py

Data is saved to trips.json next to this file.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path(_file_).with_name("trips.json")
ITIN_COLS = ["Day", "Time", "Activity", "Place", "Cost"]
PACK_COLS = ["Item", "Packed"]


def load_trips() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}


def save_trips(trips: dict) -> None:
    DATA_FILE.write_text(json.dumps(trips, indent=2), encoding="utf-8")


st.set_page_config(page_title="Travel Planner", page_icon="🧳", layout="wide")
st.title("🧳 Travel Planner")

trips = load_trips()

# ---------- Sidebar: create / choose trip ----------
with st.sidebar:
    st.header("New trip")
    with st.form("new_trip", clear_on_submit=True):
        name = st.text_input("Trip name")
        destination = st.text_input("Destination")
        start = st.date_input("Start date", date.today())
        end = st.date_input("End date", date.today() + timedelta(days=4))
        budget = st.number_input("Budget", min_value=0.0, step=500.0)
        if st.form_submit_button("Add trip"):
            if not name.strip():
                st.error("Give the trip a name.")
            elif name in trips:
                st.error("A trip with that name already exists.")
            elif end < start:
                st.error("End date must be after start date.")
            else:
                trips[name] = {
                    "destination": destination,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "budget": budget,
                    "itinerary": [],
                    "packing": [],
                }
                save_trips(trips)
                st.rerun()

    if trips:
        st.divider()
        choice = st.selectbox("Open trip", list(trips))
        if st.button("Delete this trip"):
            del trips[choice]
            save_trips(trips)
            st.rerun()

if not trips:
    st.info("Create your first trip from the sidebar to get started.")
    st.stop()

trip = trips[choice]
start_d = date.fromisoformat(trip["start"])
end_d = date.fromisoformat(trip["end"])
n_days = (end_d - start_d).days + 1

st.subheader(f"{choice} - {trip['destination'] or 'Destination not set'}")
st.caption(f"{start_d:%d %b %Y} to {end_d:%d %b %Y} ({n_days} days)")

tab_itin, tab_budget, tab_pack = st.tabs(["🗓️ Itinerary", "💰 Budget", "🎒 Packing list"])

# ---------- Itinerary ----------
with tab_itin:
    df = pd.DataFrame(trip["itinerary"], columns=ITIN_COLS)
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"itin_{choice}",
        column_config={
            "Day": st.column_config.NumberColumn(min_value=1, max_value=n_days, step=1, default=1),
            "Cost": st.column_config.NumberColumn(min_value=0, format="%.2f", default=0),
        },
    )
    if st.button("Save itinerary"):
        clean = edited.dropna(how="all").fillna(
            {"Day": 1, "Time": "", "Activity": "", "Place": "", "Cost": 0}
        )
        clean = clean.sort_values(["Day", "Time"])
        trip["itinerary"] = clean.to_dict("records")
        save_trips(trips)
        st.success("Itinerary saved.")
        st.rerun()

    if trip["itinerary"]:
        st.markdown("#### Day-by-day view")
        for day in range(1, n_days + 1):
            items = [i for i in trip["itinerary"] if int(i["Day"]) == day]
            if items:
                st.markdown(f"*Day {day} - {start_d + timedelta(days=day - 1):%a, %d %b}*")
                for i in items:
                    st.write(f"- {i['Time']} {i['Activity']} @ {i['Place']}")

# ---------- Budget ----------
with tab_budget:
    new_budget = st.number_input("Total budget", min_value=0.0, step=500.0, value=float(trip["budget"]))
    if new_budget != trip["budget"]:
        trip["budget"] = new_budget
        save_trips(trips)

    spent = sum(float(i["Cost"]) for i in trip["itinerary"])
    remaining = trip["budget"] - spent
    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", f"{trip['budget']:,.0f}")
    c2.metric("Planned spend", f"{spent:,.0f}")
    c3.metric("Remaining", f"{remaining:,.0f}", delta=f"{remaining:,.0f}")

    if trip["budget"] > 0:
        st.progress(min(spent / trip["budget"], 1.0))
        if remaining < 0:
            st.warning("You're over budget.")

    if trip["itinerary"]:
        per_day = pd.DataFrame(trip["itinerary"]).groupby("Day")["Cost"].sum()
        st.bar_chart(per_day)

# ---------- Packing ----------
with tab_pack:
    pdf = pd.DataFrame(trip["packing"], columns=PACK_COLS)
    pedited = st.data_editor(
        pdf,
        num_rows="dynamic",
        use_container_width=True,
        key=f"pack_{choice}",
        column_config={"Packed": st.column_config.CheckboxColumn(default=False)},
    )
    if st.button("Save packing list"):
        clean = pedited.dropna(how="all").fillna({"Item": "", "Packed": False})
        trip["packing"] = clean.to_dict("records")
        save_trips(trips)
        st.success("Packing list saved.")
        st.rerun()

    if trip["packing"]:
        done = sum(1 for p in trip["packing"] if p["Packed"])
        st.progress(done / len(trip["packing"]), text=f"{done}/{len(trip['packing'])} packed")
this is the code
