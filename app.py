"""A beginner-friendly Streamlit dashboard for tracking job applications."""

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


# Keep the database path stable whether Streamlit is launched from this folder or the project root.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "placements.db"
STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def create_database_table():
    """Create the applications table if it does not already exist."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                job_role TEXT,
                application_date TEXT,
                status TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def add_application(company_name, job_role, application_date, status):
    """Save one application using placeholders to safely pass values to SQLite."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications (company_name, job_role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


def load_applications():
    """Return all saved applications as a DataFrame for display and summaries."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT application_id, company_name, job_role, application_date, status
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """,
            connection,
        )
    finally:
        connection.close()


def render_add_application_form():
    """Show the form and save a new application when it is valid."""
    with st.form("add_application_form", clear_on_submit=True):
        company_name = st.text_input("Company Name")
        job_role = st.text_input("Job Role")
        application_date = st.date_input("Application Date", value=date.today())
        status = st.selectbox("Status", STATUSES)
        submitted = st.form_submit_button("Add Application", type="primary")

    if submitted:
        if not company_name.strip():
            st.error("Please enter a company name.")
        elif not job_role.strip():
            st.error("Please enter a job role.")
        else:
            add_application(
                company_name.strip(),
                job_role.strip(),
                application_date.isoformat(),
                status,
            )
            st.session_state["application_added"] = True
            st.rerun()


def render_applications_table(applications):
    """Show all saved applications, or a helpful empty-state message."""
    if applications.empty:
        st.info("No applications have been added yet. Add your first one to get started.")
        return

    display_data = applications.rename(
        columns={
            "application_id": "Application ID",
            "company_name": "Company Name",
            "job_role": "Job Role",
            "application_date": "Application Date",
            "status": "Status",
        }
    )
    st.dataframe(display_data, hide_index=True, width="stretch")


def render_insights(applications):
    """Show the most-applied role and status totals with a bar chart."""
    if applications.empty:
        st.info("Add an application to see your role and status insights.")
        return

    role_counts = applications["job_role"].value_counts()
    highest_count = int(role_counts.max())
    tied_roles = sorted(
        role_counts[role_counts == highest_count].index.tolist(),
        key=lambda role: (role.casefold(), role),
    )
    if len(tied_roles) == 1:
        st.metric("Most Applied Role", tied_roles[0], f"{highest_count} applications")
    else:
        st.metric(
            "Most Applied Role",
            tied_roles[0],
            f"{highest_count} applications (alphabetical tie-break)",
        )
        st.caption(
            "Also tied: " + ", ".join(tied_roles[1:])
        )

    recorded_status_counts = applications["status"].value_counts()
    status_summary = pd.DataFrame(
        {
            "Status": STATUSES,
            "Applications": [
                int(recorded_status_counts.get(status, 0)) for status in STATUSES
            ],
        }
    )

    st.subheader("Status-wise Summary")
    st.dataframe(status_summary, hide_index=True, width="stretch")
    st.bar_chart(status_summary.set_index("Status"))


def main():
    """Build the Placement Application Tracker page."""
    st.set_page_config(
        page_title="Placement Application Tracker",
        page_icon="📋",
        layout="wide",
    )
    create_database_table()

    st.title("📋 Placement Application Tracker")
    st.write("Keep your job applications organized and follow your progress.")

    if st.session_state.pop("application_added", False):
        st.success("Application added successfully.")

    applications = load_applications()
    total_applications = len(applications)
    st.metric("Total Applications", total_applications)

    add_tab, view_tab, insights_tab = st.tabs(
        ["Add Application", "View Applications", "Insights"]
    )

    with add_tab:
        st.subheader("Add a new application")
        render_add_application_form()

    with view_tab:
        st.subheader("Your applications")
        render_applications_table(applications)

    with insights_tab:
        st.subheader("Application insights")
        render_insights(applications)


if __name__ == "__main__":
    main()
