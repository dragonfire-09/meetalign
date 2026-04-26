import streamlit as st
import pandas as pd
from database import init_db, add_availability, get_availability

init_db()

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide"
)

st.title("📅 MeetAlign")
st.caption("Smart meeting availability tool for project teams")

menu = st.sidebar.radio(
    "Menu",
    ["Create Meeting", "Add Availability", "View Matches"]
)

if menu == "Create Meeting":
    st.header("Create Meeting")

    meeting_id = st.number_input(
        "Choose Meeting ID",
        min_value=1,
        step=1
    )

    meeting_title = st.text_input(
        "Meeting Title",
        placeholder="EIC Pathfinder Collaboration Meeting"
    )

    if st.button("Create Meeting"):
        if meeting_title:
            st.success("Meeting created successfully.")
            st.info(f"Share this Meeting ID: {meeting_id}")
        else:
            st.warning("Please enter a meeting title.")

elif menu == "Add Availability":
    st.header("Add Availability")

    meeting_id = st.number_input(
        "Meeting ID",
        min_value=1,
        step=1
    )

    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    role = st.selectbox("Role", ["Organizer", "Participant"])

    date = st.date_input("Available Date")
    start_time = st.time_input("Start Time")
    end_time = st.time_input("End Time")

    if st.button("Save Availability"):
        if not name:
            st.warning("Please enter your name.")
        elif start_time >= end_time:
            st.warning("End time must be later than start time.")
        else:
            add_availability(
                meeting_id,
                name,
                email,
                role,
                date,
                start_time,
                end_time
            )
            st.success("Availability saved successfully.")

elif menu == "View Matches":
    st.header("View Matches")

    meeting_id = st.number_input(
        "Meeting ID",
        min_value=1,
        step=1,
        key="match_meeting_id"
    )

    rows = get_availability(meeting_id)

    if rows:
        df = pd.DataFrame(
            rows,
            columns=[
                "Name",
                "Email",
                "Role",
                "Date",
                "Start Time",
                "End Time"
            ]
        )

        st.subheader("All Availability")
        st.dataframe(df, use_container_width=True, hide_index=True)

        organizer_df = df[df["Role"] == "Organizer"]
        participant_df = df[df["Role"] == "Participant"]

        matches = []

        for _, organizer in organizer_df.iterrows():
            for _, participant in participant_df.iterrows():
                if organizer["Date"] == participant["Date"]:
                    latest_start = max(
                        organizer["Start Time"],
                        participant["Start Time"]
                    )
                    earliest_end = min(
                        organizer["End Time"],
                        participant["End Time"]
                    )

                    if latest_start < earliest_end:
                        matches.append({
                            "Date": organizer["Date"],
                            "Available From": latest_start,
                            "Available Until": earliest_end,
                            "Organizer": organizer["Name"],
                            "Participant": participant["Name"]
                        })

        st.subheader("Matching Time Slots")

        if matches:
            st.success("Matching slots found.")
            st.dataframe(
                pd.DataFrame(matches),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No matching time slots found yet.")
    else:
        st.info("No availability has been added for this meeting yet.")
