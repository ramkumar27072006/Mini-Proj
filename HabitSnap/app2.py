import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid

# -----------------------------------
# 🔐 Load Firebase credentials securely from Streamlit secrets
# -----------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["FIREBASE"]["type"],
        "project_id": st.secrets["FIREBASE"]["project_id"],
        "private_key_id": st.secrets["FIREBASE"]["private_key_id"],
        "private_key": st.secrets["FIREBASE"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["FIREBASE"]["client_email"],
        "client_id": st.secrets["FIREBASE"]["client_id"],
        "auth_uri": st.secrets["FIREBASE"]["auth_uri"],
        "token_uri": st.secrets["FIREBASE"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["FIREBASE"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["FIREBASE"]["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred, {
        'storageBucket': st.secrets["FIREBASE"]["storage_bucket"]
    })

db = firestore.client()
bucket = storage.bucket()

# -----------------------------------
# 🖥️ UI Setup
# -----------------------------------
st.set_page_config(page_title="📸 HabitSnap Cloud", page_icon="📸")
st.title("📸 HabitSnap (Secure Firebase Version)")
st.markdown("Track your habits securely in the cloud with your personal login.")

# -----------------------------------
# 👤 User Login (by username)
# -----------------------------------
st.header("🔐 User Login")
username = st.text_input("Choose your unique username:")
login = st.button("Login")

if login and username:
    st.session_state.username = username.strip().lower()
    st.success(f"Welcome, {st.session_state.username}!")

# -----------------------------------
# 📝 Add New Habit Entry
# -----------------------------------
if "username" in st.session_state:
    st.markdown("---")
    st.subheader("➕ Add New Entry")

    with st.form("entry_form", clear_on_submit=True):
        habit_text = st.text_input("Describe your habit:")
        photo_file = st.file_uploader("Upload a photo (optional):", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Add Entry")

        if submitted and habit_text:
            photo_url = None
            if photo_file:
                blob_path = f"users/{st.session_state.username}/{uuid.uuid4()}.jpg"
                blob = bucket.blob(blob_path)
                blob.upload_from_file(photo_file, content_type=photo_file.type)
                blob.make_public()
                photo_url = blob.public_url

            db.collection("users").document(st.session_state.username).collection("habits").add({
                "text": habit_text,
                "timestamp": datetime.utcnow(),
                "photo": photo_url
            })
            st.success("Habit entry added!")

    # -----------------------------------
    # 📅 View Existing Entries
    # -----------------------------------
    st.markdown("---")
    st.subheader("📅 Your Habit Log")

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
