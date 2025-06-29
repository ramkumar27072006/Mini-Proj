
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import base64
import uuid
import os

# Load Firebase credentials
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")  # <-- Replace with your own config file
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'your-project-id.appspot.com'  # <-- Replace with your own bucket
    })

db = firestore.client()
bucket = storage.bucket()

st.set_page_config(page_title="📸 HabitSnap Cloud", page_icon="📸")
st.title("📸 HabitSnap (with Firebase)")
st.markdown("Your habits are now securely stored in the cloud, per user!")

# ------------------- USER LOGIN -------------------
st.header("🔐 User Login")
username = st.text_input("Choose a unique username:")
login = st.button("Login")

if login and username:
    st.session_state.username = username.strip().lower()
    st.success(f"Welcome, {st.session_state.username}!")

# Proceed only if user is logged in
if "username" in st.session_state:
    st.markdown("---")
    st.subheader("➕ Add New Habit Entry")

    with st.form("entry_form", clear_on_submit=True):
        habit_text = st.text_input("Describe your habit:")
        photo_file = st.file_uploader("Upload a photo (optional):", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Add Entry")

        if submitted and habit_text:
            photo_url = None
            if photo_file:
                # Save photo to Firebase Storage
                blob_path = f"users/{st.session_state.username}/{uuid.uuid4()}.jpg"
                blob = bucket.blob(blob_path)
                blob.upload_from_file(photo_file, content_type=photo_file.type)
                blob.make_public()
                photo_url = blob.public_url

            # Save habit entry in Firestore
            db.collection("users").document(st.session_state.username)                .collection("habits").add({
                    "text": habit_text,
                    "timestamp": datetime.utcnow(),
                    "photo": photo_url
                })
            st.success("Habit entry added!")

    # ------------------- VIEW ENTRIES -------------------
    st.markdown("---")
    st.subheader("📅 Your Habit Entries")

    habits_ref = db.collection("users").document(st.session_state.username).collection("habits")
    habits = habits_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

    grouped = {}
    for doc in habits:
        entry = doc.to_dict()
        dt = entry["timestamp"].astimezone()
        month_key = dt.strftime("%B %Y")
        grouped.setdefault(month_key, []).append((dt, entry["text"], entry.get("photo"), doc.id))

    for month, entries in grouped.items():
        with st.expander(f"📆 {month}", expanded=False):
            for dt, text, photo, doc_id in entries:
                st.markdown(f"**{dt.strftime('%d %b %Y %I:%M %p')}** - {text}")
                if photo:
                    st.image(photo, width=200)
                if st.button("Delete", key=doc_id):
                    habits_ref.document(doc_id).delete()
                    st.experimental_rerun()
