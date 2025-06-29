import streamlit as st
from firebase_admin import credentials, firestore, storage, initialize_app
import firebase_admin
import pandas as pd
from datetime import datetime, timedelta
import uuid

# Firebase Init
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
    initialize_app(cred, {
        'storageBucket': st.secrets["FIREBASE"]["storage_bucket"]
    })

db = firestore.client()
bucket = storage.bucket()

# App config
st.set_page_config(page_title="HabitSnap Pro", layout="wide")

# Theme Switch
theme = st.sidebar.radio("🌗 Theme", ["🌞 Light", "🌙 Dark"])
dark = theme == "🌙 Dark"
st.markdown(f"""
    <style>
    body {{
        background-color: {"#0f2027" if dark else "#ffffff"};
        color: {"#ffffff" if dark else "#000000"};
    }}
    </style>
""", unsafe_allow_html=True)

# Google Auth (simplified)
st.sidebar.title("🔐 Sign In")
email = st.sidebar.text_input("Your Google Email")
uid = st.sidebar.text_input("Firebase UID")
username = email.split('@')[0] if email else "unknown"

if not email or not uid:
    st.warning("Enter authenticated email & UID.")
    st.stop()

is_admin = username == "ramkumar27"
st.sidebar.success(f"✅ Signed in as {username}")

# Entry Form
st.title("📋 HabitSnap - Tracker")
st.subheader("➕ Add a New Habit")
with st.form("habit_form", clear_on_submit=True):
    text = st.text_input("Describe your habit:")
    photo = st.file_uploader("Optional Photo", type=["jpg", "png", "jpeg"])
    submitted = st.form_submit_button("Add Entry")

    if submitted and text:
        photo_url = None
        if photo:
            blob_path = f"users/{username}/{uuid.uuid4()}.jpg"
            blob = bucket.blob(blob_path)
            blob.upload_from_file(photo, content_type=photo.type)
            blob.make_public()
            photo_url = blob.public_url
        db.collection("users").document(username).collection("habits").add({
            "text": text,
            "timestamp": datetime.utcnow(),
            "photo": photo_url
        })
        st.success("Habit entry added!")

# View Log
st.markdown("---")
st.subheader("📅 Your Habit History")
ref = db.collection("users").document(username).collection("habits")
docs = list(ref.order_by("timestamp", direction=firestore.Query.DESCENDING).stream())

grouped = {}
dates_logged = set()

for doc in docs:
    data = doc.to_dict()
    ts = data["timestamp"].astimezone()
    dates_logged.add(ts.date())
    month = ts.strftime("%B %Y")
    grouped.setdefault(month, []).append((ts, data["text"], data.get("photo"), doc.id))

# Streak Calculation
today = datetime.now().date()
streak = 0
for i in range(100):
    if (today - timedelta(days=i)) in dates_logged:
        streak += 1
    else:
        break

st.info(f"🔥 Current Streak: **{streak}** days")
st.info(f"📈 Total Entries: **{len(docs)}**")
if len(docs) >= 10:
    st.success("🏅 Badge: 10+ Logs!")

for month, entries in grouped.items():
    with st.expander(f"📆 {month}", expanded=False):
        for dt, txt, photo, docid in entries:
            st.markdown(f"🕒 {dt.strftime('%d %b %Y %I:%M %p')} - **{txt}**")
            if photo:
                st.image(photo, width=200)
            if st.button("🗑️ Delete", key=docid):
                ref.document(docid).delete()
                st.experimental_rerun()

# Admin Dashboard
if is_admin:
    st.title("🔍 Admin Dashboard")
    all_entries = []
    users = db.collection("users").stream()
    for u in users:
        uref = db.collection("users").document(u.id).collection("habits").stream()
        for d in uref:
            data = d.to_dict()
            all_entries.append({
                "username": u.id,
                "timestamp": data["timestamp"].astimezone().strftime("%Y-%m-%d %H:%M"),
                "text": data["text"],
                "photo": data.get("photo", "")
            })

    df = pd.DataFrame(all_entries)
    if df.empty:
        st.warning("No data found.")
    else:
        user_filter = st.selectbox("👤 Filter by user", ["All"] + df["username"].unique().tolist())
        if user_filter != "All":
            df = df[df["username"] == user_filter]
        st.dataframe(df, use_container_width=True)

        if st.button("📥 Export All"):
            st.download_button("Download CSV", df.to_csv(index=False), file_name="all_logs.csv")

        st.markdown("🖼️ Image Gallery")
        for _, row in df.iterrows():
            if row["photo"]:
                with st.expander(f"{row['username']} - {row['timestamp']}"):
                    st.markdown(f"📝 {row['text']}")
                    st.image(row["photo"], use_column_width=True)
