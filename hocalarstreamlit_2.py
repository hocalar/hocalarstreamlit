import streamlit as st
import pandas as pd
from io import BytesIO
import gspread
from google.colab import auth
from google.auth import default

# Google Sheets yetkilendirme
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

def read_last_sheet_as_df(spreadsheet_id):
    try:
        sh = gc.open_by_key(spreadsheet_id)
        last_sheet = sh.worksheets()[-1]  # Son sayfa
        data = last_sheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Son sheet alınamadı: {e}")
        return pd.DataFrame()

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.set_page_config(layout="wide")
st.markdown("""
<h1 style='color:#2E86C1;'>📈 Hocalar Hisse Verileri Analizi</h1>
<hr style='height:2px;border:none;color:#2E86C1;background-color:#2E86C1;' />
""", unsafe_allow_html=True)

# Google Sheets dosyalarının ID’leri
sheet1_id = "1u9WT-P9dEoXYuCOX1ojkFUySeJVmznc6dEFzhq0Ob8M"
sheet2_id = "1MnhlPTx6aD5a4xuqsVLRw3ktLmf-NwSpXtw_IteXIFs"

# En son sayfaları oku
df1 = read_last_sheet_as_df(sheet1_id)
df2 = read_last_sheet_as_df(sheet2_id)

# Ticker isimlerini düzelt
if "Ticker" in df1.columns:
    df1 = df1.rename(columns={"Ticker": "Hisse Adı"})
if "Ticker" in df2.columns:
    df2 = df2.rename(columns={"Ticker": "Hisse Adı"})

# Period sadece df1'den alınacak
period_df = df1[["Hisse Adı", "Period"]] if "Period" in df1.columns else pd.DataFrame()

# Birleştirme işlemi
if "Hisse Adı" in df1.columns and "Hisse Adı" in df2.columns:
    df = pd.merge(df2, df1.drop(columns=["Period"], errors="ignore"), on="Hisse Adı", how="outer")
    if not period_df.empty:
        df = pd.merge(df, period_df, on="Hisse Adı", how="left")
else:
    st.error(f"'Hisse Adı' sütunu her iki tabloda da olmalı.\nSheet1: {list(df1.columns)}\nSheet2: {list(df2.columns)}")
    st.stop()

df = df.fillna("N/A")

# Hedef kolonlar
target_columns = [
    "Hisse Adı", "ATH Değişimi TL (%)", "Geçen Gün", "AVWAP +4σ",
    "% Fark VWAP", "% Fark POC", "% Fark VAL", "VAH / VAL Yüzdesi (%)", "VP Bant / ATH Aralığı (%)",
    "Period", "Ortalama Hedef Fiyat", "OHD - USD", "Hisse Potansiyeli (Yüzde)", "YDF Oranı", "Özkaynak Karlılığı", "Yıllık Net Kar",
    "Borç Özkaynak Oranı", "Ödenmiş Sermaye", "FD/FAVÖK",
    "ROIC Oranı", "Cari Oran", "Net Borç/Favök"
]
df = df[[col for col in target_columns if col in df.columns]]

# Sidebar filtreler
st.sidebar.header("Filtreler")

# Görünür kolon seçimi
selected_columns = st.sidebar.multiselect(
    "Görünmesini istediğiniz kolonları seçin",
    options=df.columns.tolist(),
    default=df.columns.tolist()
)

# Sayısal kolonlar için slider filtre
for col in df.columns:
    if col == "Hisse Adı" or col == "Period":
        continue
    try:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].notna().sum() > 0:
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            if min_val != max_val:
                selected_range = st.sidebar.slider(
                    col, min_value=min_val, max_value=max_val,
                    value=(min_val, max_val),
                    step=(max_val - min_val) / 100
                )
                df = df[df[col].between(*selected_range)]
    except:
        continue

# Gösterim
st.subheader("Filtrelenmiş Veri Tablosu")
st.dataframe(df[selected_columns], use_container_width=True)

# Excel indirme
st.download_button("Excel olarak indir",
                   convert_df_to_excel(df[selected_columns]),
                   file_name="hisse_analizi_filtered.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
