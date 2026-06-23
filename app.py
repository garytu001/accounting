import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="管報自動化系統", layout="wide")

st.title("📊 管報自動化：雲端報表生成器")
st.markdown("上傳明細資料後，系統將自動彙總並**直接更新至指定的 Google Sheets**。")

# 設定您的目標 Google Sheets 網址 (請替換為您實際的網址)
TARGET_SHEET_URL = "https://docs.google.com/spreadsheets/d/您的試算表ID/edit"

# --- 步驟 1：檔案上傳 ---
uploaded_file = st.file_uploader("上傳 01.管報主檔-明細資料", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 讀取檔案
    with st.spinner("資料讀取中..."):
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
    st.success(f"成功讀取檔案！共 {len(df)} 筆資料。")

    # --- 步驟 2：設定彙總邏輯 ---
    st.subheader("⚙️ 報表彙總運算")
    
    col1, col2 = st.columns(2)
    with col1:
        default_group = [col for col in ['會計科目', '期間', '月份'] if col in df.columns]
        group_cols = st.multiselect("分類維度", options=df.columns, default=default_group)
        
    with col2:
        default_val = [col for col in ['金額', '本期發生額'] if col in df.columns]
        val_col = st.selectbox("數值欄位", options=df.columns, index=df.columns.get_loc(default_val[0]) if default_val else 0)

    # --- 步驟 3：產出與寫入 Google Sheets ---
    if group_cols and val_col:
        company_df = df.groupby(group_cols)[val_col].sum().reset_index()
        st.dataframe(company_df.head(5), use_container_width=True) # 預覽前五筆
        
        # 觸發寫入動作的按鈕
        if st.button("🚀 彙總並寫入 Google Sheets", type="primary"):
            with st.spinner("正在連線 Google API 並寫入資料庫..."):
                try:
                    # 1. 建立 GCP 憑證授權 (讀取 Streamlit Secrets)
                    scopes = [
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                    creds = Credentials.from_service_account_info(
                        st.secrets["gcp_service_account"], 
                        scopes=scopes
                    )
                    client = gspread.authorize(creds)

                    # 2. 開啟目標 Google Sheets
                    spreadsheet = client.open_by_url(TARGET_SHEET_URL)

                    # 3. 指定工作表 (Sheet name)
                    # 建議寫入一個隱藏的 Raw Data 表，不要直接蓋掉主管看的
