import streamlit as st
import pandas as pd
import io

# 設定網頁標題與寬度
st.set_page_config(page_title="管報自動化系統", layout="wide")

st.title("📊 管報自動化：全公司報表生成器")
st.markdown("請上傳 `01.管報主檔` 中的 **明細資料**，系統將自動彙總並產出 **全公司** 視角的財務報表。")

# --- 步驟 1：檔案上傳 ---
uploaded_file = st.file_uploader("上傳明細資料 (支援 CSV 或 Excel 格式)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # 讀取檔案
        with st.spinner("資料讀取中..."):
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
                
        st.success(f"成功讀取檔案！共 {len(df)} 筆資料。")
        
        with st.expander("預覽原始明細資料"):
            st.dataframe(df.head(10))

        # --- 步驟 2：設定彙總邏輯 (ETL Transform) ---
        st.subheader("⚙️ 設定報表彙總邏輯")
        
        col1, col2 = st.columns(2)
        with col1:
            # 讓使用者選擇要 GroupBy 的欄位 (例如：會計科目、發生期間)
            # 預設嘗試抓取常見的欄位名稱，若無則留空
            default_group = [col for col in ['會計科目', '科目名稱', '期間', '月份'] if col in df.columns]
            group_cols = st.multiselect(
                "1. 選擇要分類的維度 (例如：期間、會計科目)", 
                options=df.columns,
                default=default_group
            )
            
        with col2:
            # 讓使用者選擇要加總的數值欄位 (例如：本期發生額)
            default_val = [col for col in ['金額', '本期發生額', '借貸淨額'] if col in df.columns]
            val_col = st.selectbox(
                "2. 選擇要加總的數值欄位 (例如：金額)", 
                options=df.columns,
                index=df.columns.get_loc(default_val[0]) if default_val else 0
            )

        # --- 步驟 3：產出與下載全公司報表 ---
        if group_cols and val_col:
            st.subheader("📈 全公司報表結果")
            
            # 執行資料樞紐/彙總運算
            # 將明細資料依據選擇的維度進行加總，抹除部門維度以達到「全公司」視角
            company_df = df.groupby(group_cols)[val_col].sum().reset_index()
            
            # 顯示結果
            st.dataframe(company_df, use_container_width=True)
            
            # 準備下載檔案 (轉為 Excel)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                company_df.to_excel(writer, index=False, sheet_name='全公司報表')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 下載全公司報表 (Excel)",
                data=excel_data,
                file_name="永悅健康全公司_自動彙總.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("請至少選擇一個分類維度與一個數值欄位來進行運算。")

    except Exception as e:
        st.error(f"處理檔案時發生錯誤：{e}")
        st.info("請檢查上傳的檔案格式是否正確，或檔案是否損毀。")
