import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from io import BytesIO

# === Google Sheets edit linkini CSV linke dönüştür ===
def convert_edit_url_to_csv(url):
    return url.split("/edit")[0] + "/export?format=csv"

# === Google Sheets'ten veri çek (herkese açık paylaşımlı link) ===
def read_public_google_sheet(csv_url, selected_columns):
    df = pd.read_csv(csv_url)
    existing_columns = [col for col in selected_columns if col in df.columns]
    missing_columns = set(selected_columns) - set(existing_columns)
    if missing_columns:
        st.warning(f"Google Sheet'te bulunmayan sütunlar: {missing_columns}")
    return df[existing_columns]

# === Excel çıktı fonksiyonu ===
def convert_df_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.close()
    return output.getvalue()

# === Sayfa başlığı ===
st.set_page_config(layout="wide")
st.title("Hocalar Hisse Analizi")

# === Google Sheets edit linkleri ===
sheet1_edit_url = "https://docs.google.com/spreadsheets/d/1MnhlPTx6aD5a4xuqsVLRw3ktLmf-NwSpXtw_IteXIFs/edit?usp=drivesdk"
sheet2_edit_url = "https://docs.google.com/spreadsheets/d/1u9WT-P9dEoXYuCOX1ojkFUySeJVmznc6dEFzhq0Ob8M/edit?usp=drivesdk"

# === CSV linke dönüştür ===
sheet1_url = convert_edit_url_to_csv(sheet1_edit_url)
sheet2_url = convert_edit_url_to_csv(sheet2_edit_url)

# === Kolon seçimleri ===
sheet1_cols = ["ATH Değişimi TL (%)", "Geçen Gün", "AVWAP", "AVWAP +4σ", "% Fark VWAP",
               "POC", "VAL", "VAH", "% Fark POC", "% Fark VAL", "VP Bant / ATH Aralığı (%)"]

sheet2_cols = ["Hisse Adı", "Sektör", "Period", "Ortalama Hedef Fiyat", "OHD - USD",
               "Hisse Potansiyeli (Yüzde)", "Hisse Puanı", "YDF Oranı", "Özkaynak Karlılığı",
               "Yıllık Net Kar", "Borç Özkaynak Oranı", "Ödenmiş Sermaye", "Bölünme",
               "Piyasa Değeri", "Peg Rasyosu", "FD/FAVÖK", "ROIC Oranı", "PD/FCF", "Cari Oran",
               "Net Borç/Favök", "F/K Oranı", "PD/DD Oranı", "Hisse Fiyatı"]

# === Verileri al ===
st.info("Hisse Temel ve Teknik Değerler Listesi")
df1 = read_public_google_sheet(sheet1_url, sheet1_cols)
df2 = read_public_google_sheet(sheet2_url, sheet2_cols)

df = pd.concat([df2, df1], axis=1)

# === Grid yapılandırması ===
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
gb.configure_selection("single", use_checkbox=True)
gb.configure_side_bar()  # Kolon ekle/kaldır menüsü

# Sayısal kolonları formatla
numeric_columns = df.select_dtypes(include="number").columns.tolist()
for col in numeric_columns:
    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2)

# === Hisse Adı sütununa hyperlink ekle (görünüm değişmeden) ===
gb.configure_column(
    "Hisse Adı",
    cellRenderer="""
        function(params) {
            const symbol = params.value.replace(/"/g, '');
            const url = `https://tr.tradingview.com/chart/hOArWHrE/?symbol=${symbol}`;
            return `<span style="cursor:pointer;"><a href="${url}" target="_blank" style="text-decoration:none;color:#1f77b4;">${params.value}</a></span>`;
        }
    """
)

grid_options = gb.build()

# === AgGrid gösterimi ===
st.subheader("Veri Tablosu")
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    height=600,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True
)

filtered_df = pd.DataFrame(grid_response["data"])

# === Excel olarak indir ===
st.download_button("Excel olarak indir (filtrelenmiş)",
                   convert_df_to_excel(filtered_df),
                   file_name="hisse_analizi_public.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
