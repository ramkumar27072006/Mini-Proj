
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
from datetime import datetime
import uuid

# ----------------- Firebase Init -----------------
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

st.set_page_config(page_title="📸 HabitSnap | Admin + User", page_icon="📸", layout="wide")

# ----------------- Sidebar Navigation -----------------
st.sidebar.title("🔀 Navigation")
page = st.sidebar.radio("Go to", ["📋 HabitSnap Tracker", "🔍 Admin Dashboard"])

# ----------------- Page 1: User Habit Tracker -----------------
if page == "📋 HabitSnap Tracker":
    st.title("📋 HabitSnap - Personal Tracker")

    username = st.text_input("👤 Enter your username:")
    if username:
        st.success(f"Logged in as `{username}`")

        st.subheader("➕ Add New Habit Entry")
        with st.form("entry_form", clear_on_submit=True):
            habit_text = st.text_input("Habit description:")
            photo_file = st.file_uploader("Photo (optional):", type=["png", "jpg", "jpeg"])
            submitted = st.form_submit_button("Add Entry")

            if submitted and habit_text:
                photo_url = None
                if photo_file:
                    blob_path = f"users/{username}/{uuid.uuid4()}.jpg"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_file(photo_file, content_type=photo_file.type)
                    blob.make_public()
                    photo_url = blob.public_url

                db.collection("users").document(username).collection("habits").add({
                    "text": habit_text,
                    "timestamp": datetime.utcnow(),
                    "photo": photo_url
                })
                st.success("✅ Habit entry added!")

        # View habits
        st.markdown("---")
        st.subheader("📅 Your Habit Log")
        habits_ref = db.collection("users").document(username).collection("habits")
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

# ----------------- Page 2: Admin Dashboard -----------------
elif page == "🔍 Admin Dashboard":
    st.title("🔍 Admin Dashboard")

    users_ref = db.collection("users").stream()
    all_data = []

    for user_doc in users_ref:
        uname = user_doc.id
        habits = db.collection("users").document(uname).collection("habits").stream()
        for doc in habits:
            d = doc.to_dict()
            all_data.append({
                "username": uname,
                "timestamp": d["timestamp"].astimezone().strftime("%Y-%m-%d %H:%M"),
                "text": d["text"],
                "photo": d.get("photo", "")
            })

    df = pd.DataFrame(all_data)
    if df.empty:
        st.warning("No data found.")
    else:
        usernames = df["username"].unique().tolist()
        selected_user = st.selectbox("Filter by user", ["All"] + usernames)
        filtered_df = df if selected_user == "All" else df[df["username"] == selected_user]

        st.dataframe(filtered_df, use_container_width=True)

        if st.button("📥 Export CSV"):
            st.download_button("Download CSV", data=filtered_df.to_csv(index=False), file_name="all_habits.csv")

        st.markdown("### 📸 Uploaded Photos")
        for i, row in filtered_df.iterrows():
            if row["photo"]:
                with st.expander(f"{row['username']} - {row['timestamp']}"):
                    st.markdown(f"**{row['text']}**")
                    st.image(row["photo"], use_column_width=True)
