import streamlit as st
import pandas as pd
from io import BytesIO

def convert_edit_url_to_csv(url):
    return url.split("/edit")[0] + "/export?format=csv"

def read_public_google_sheet(csv_url):
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Veri alınamadı: {e}")
        return pd.DataFrame()

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.set_page_config(layout="wide")
st.title("Hocalar Hisse Verileri Analizi")

# Google Sheets CSV linkleri
sheet1_url = convert_edit_url_to_csv("https://docs.google.com/spreadsheets/d/1u9WT-P9dEoXYuCOX1ojkFUySeJVmznc6dEFzhq0Ob8M/edit?usp=drivesdk")
sheet2_url = convert_edit_url_to_csv("https://docs.google.com/spreadsheets/d/1MnhlPTx6aD5a4xuqsVLRw3ktLmf-NwSpXtw_IteXIFs/edit?usp=drivesdk")

df1 = read_public_google_sheet(sheet1_url)
df2 = read_public_google_sheet(sheet2_url)

if "Ticker" in df1.columns:
    df1 = df1.rename(columns={"Ticker": "Hisse Adı"})
if "Ticker" in df2.columns:
    df2 = df2.rename(columns={"Ticker": "Hisse Adı"})

# Period sadece df1'den alınacak
period_df = df1[["Hisse Adı", "Period"]] if "Period" in df1.columns else pd.DataFrame()

# Merge işlemi
if "Hisse Adı" in df1.columns and "Hisse Adı" in df2.columns:
    df = pd.merge(df2, df1.drop(columns=["Period"], errors="ignore"), on="Hisse Adı", how="outer")
    if not period_df.empty:
        df = pd.merge(df, period_df, on="Hisse Adı", how="left")
else:
    st.error(f"'Hisse Adı' sütunu her iki tabloda da olmalı.\nSheet1: {list(df1.columns)}\nSheet2: {list(df2.columns)}")
    st.stop()

df = df.fillna("N/A")

# İstenen kolonlar
target_columns = [
    "Hisse Adı", "ATH Değişimi TL (%)", "Geçen Gün", "AVWAP +4σ",
    "% Fark VWAP", "% Fark POC", "% Fark VAL", "VAH / VAL Yüzdesi (%)", "VP Bant / ATH Aralığı (%)",
    "Period", "Ortalama Hedef Fiyat", "OHD - USD", "Hisse Potansiyeli (Yüzde)", "YDF Oranı", "Özkaynak Karlılığı", "Yıllık Net Kar", 
    "Borç Özkaynak Oranı", "Ödenmiş Sermaye", "FD/FAVÖK",
    "ROIC Oranı", "Cari Oran", "Net Borç/Favök"
]
df = df[[col for col in target_columns if col in df.columns]]

st.sidebar.header("Filtreler")

# Görünür kolonlar filtresi (çoklu seçim)
selected_columns = st.sidebar.multiselect(
    "Görünmesini istediğiniz kolonları seçin",
    options=df.columns.tolist(),
    default=df.columns.tolist()
)

# Diğer tüm kolonlar için slider filtreler
#for col in df.columns:
#    if col == "Hisse Adı" or col == "Period":
#        continue
#    try:
#        df[col] = pd.to_numeric(df[col], errors="coerce")
#        if df[col].notna().sum() > 0:
#            min_val = float(df[col].min())
#            max_val = float(df[col].max())
#            if min_val != max_val:
#                selected_range = st.sidebar.slider(
#                    col, min_value=min_val, max_value=max_val,
#                    value=(min_val, max_val),
#                    step=(max_val - min_val) / 100
#                )
#                df = df[df[col].between(*selected_range)]
#    except:
#        continue

# Sayısal filtreler
for col in df.select_dtypes(include='number').columns:
    min_val = float(df[col].min())
    max_val = float(df[col].max())
    selected_range = st.sidebar.slider(
        f"{col}", min_value=min_val, max_value=max_val,
        value=(min_val, max_val),
        step=(max_val - min_val) / 100 if max_val != min_val else 1.0
    )

    # Filtrele ama NaN olanları bırak
    df = df[df[col].between(*selected_range) | df[col].isna()]
        
# Tablo gösterimi
st.subheader("Filtrelenmiş Veri Tablosu")
st.dataframe(df[selected_columns], use_container_width=True)

# Excel indirme
st.download_button("Excel olarak indir",
                   convert_df_to_excel(df[selected_columns]),
                   file_name="hisse_analizi_filtered.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
