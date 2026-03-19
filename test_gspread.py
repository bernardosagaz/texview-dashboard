import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

try:
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    
    SHEET_ID = "1DR9IRu6rItkOUvGBPtZqHoA8p6kiC"
    print(f"Trying to open sheet ID: {SHEET_ID}")
    sh = gc.open_by_key(SHEET_ID)
    print(f"Success! Found sheet title: {sh.title}")
    
    print("Worksheets:")
    for ws in sh.worksheets():
        print(f" - {ws.title}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
