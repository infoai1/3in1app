import streamlit as st
import pandas as pd
import schedule
import time
import threading

def export_files(df):
    # CSV export
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="processed.csv",
        mime="text/csv"
    )

    # Main JSON export
    main_json = df.to_json(orient="records")
    st.download_button(
        label="Download Main JSON",
        data=main_json,
        file_name="main.json",
        mime="application/json"
    )

    # References JSON export
    if 'extracted_data' in df.columns:
        refs_df = pd.DataFrame({"extracted_data": df["extracted_data"]})
        refs_json = refs_df.to_json(orient="records")
        st.download_button(
            label="Download Refs JSON",
            data=refs_json,
            file_name="refs.json",
            mime="application/json"
        )

def download_csv(df, filename):
    csv = df.to_csv(index=False)
    st.download_button(
        label=f"Download {filename}",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )

def schedule_off_peak():
    def job():
        st.write("Running off-peak job...")

    schedule.every().day.at("22:00").do(job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

    threading.Thread(target=run_scheduler, daemon=True).start()
    st.write("Scheduler started for off-peak.")
