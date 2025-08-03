import streamlit as st
import pandas as pd
import schedule
import time
import threading

def export_files(df):
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "processed.csv")
    
    # Main JSON: Chunks with metadata
    main_json = df.to_json(orient="records")
    st.download_button("Download Main JSON", main_json, "main.json")
    
    # Refs JSON: Dedicated for references/footnotes
    refs_df = pd.DataFrame({"extracted_data": df["extracted_data"]})  # Expand with more logic if needed
    refs_json = refs_df.to_json(orient="records")
    st.download_button("Download Refs JSON", refs_json, "refs.json")

def schedule_off_peak():
    def job():
        # Placeholder: Run full processing (call functions from other files)
        st.write("Running off-peak job...")
    
    schedule.every().day.at("22:00").do(job)  # 10 PM IST
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    threading.Thread(target=run_scheduler, daemon=True).start()
    st.write("Scheduler started for off-peak.")
