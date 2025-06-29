
import streamlit as st
from datetime import datetime
import pandas as pd
import base64

st.set_page_config(page_title="📸 HabitSnap", page_icon="📸")

st.title("📸 HabitSnap - Streamlit Version")
st.markdown("Track your habits daily with optional photo proof. Data is saved only during your session.")

# Initialize session state
if "habits" not in st.session_state:
    st.session_state.habits = []

# Input fields
with st.form("habit_form", clear_on_submit=True):
    habit_text = st.text_input("Enter your habit:")
    photo_file = st.file_uploader("Upload photo (optional):", type=["jpg", "png"])
    submitted = st.form_submit_button("Add Entry")

    if submitted and habit_text:
        photo_data = None
        if photo_file is not None:
            photo_bytes = photo_file.read()
            photo_data = base64.b64encode(photo_bytes).decode("utf-8")

        entry = {
            "text": habit_text,
            "timestamp": datetime.now().isoformat(),
            "photo": photo_data
        }
        st.session_state.habits.append(entry)
        st.success("Habit entry added!")

# Group entries by month
def group_by_month(entries):
    grouped = {}
    for entry in entries:
        dt = datetime.fromisoformat(entry["timestamp"])
        key = dt.strftime("%B %Y")
        grouped.setdefault(key, []).append(entry)
    return grouped

st.markdown("---")
st.header("📅 Monthly Habit Log")

if not st.session_state.habits:
    st.info("No entries yet. Start adding habits above!")
else:
    grouped = group_by_month(st.session_state.habits)
    for month, entries in grouped.items():
        with st.expander(f"📆 {month}", expanded=False):
            for i, entry in enumerate(entries):
                dt = datetime.fromisoformat(entry["timestamp"]).strftime("%d %b %Y, %I:%M %p")
                st.markdown(f"**{dt}** - {entry['text']}")
                if entry["photo"]:
                    st.image(base64.b64decode(entry["photo"]), width=150)
                if st.button(f"Delete", key=f"delete_{month}_{i}"):
                    st.session_state.habits.remove(entry)
                    st.rerun()
