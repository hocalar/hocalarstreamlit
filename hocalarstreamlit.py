import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from io import BytesIO
import base64
import gspread
from google.oauth2.service_account import Credentials

# === Google API kimlik doğrulama: base64 encoded credentials.json ===
def get_gspread_client():
    encoded = st.secrets["google"]["credentials"]
    decoded = base64.b64decode(encoded)
    creds = Credentials.from_service_account_info(eval(decoded.decode()))
    return gspread.authorize(creds)

# === Google Sheets verisini oku ===
def read_google_sheet(sheet_id, worksheet_index_or_title, selected_columns):
    gc = get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    ws = sh.get_worksheet(worksheet_index_or_title) if isinstance(worksheet_index_or_title, int) else sh.worksheet(worksheet_index_or_title)
    df = pd.DataFrame(ws.get_all_records())
    existing_columns = [col for col in selected_columns if col in df.columns]
    missing = set(selected_columns) - set(existing_columns)
    if missing:
        st.warning(f"Eksik kolonlar: {missing}")
    return df[existing_columns]

# === Excel çıktı fonksiyonu ===
def convert_df_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False)
    writer.close()
    return output.getvalue()

# === Sayfa ayarı ===
st.set_page_config(layout="wide")
st.title("Hocalar Hisse Analizi")

# === secrets.toml'dan sheet ID'leri ===
sheet1_id = st.secrets["sheets"]["sheet1_id"]
sheet2_id = st.secrets["sheets"]["sheet2_id"]

# === Kolonlar ===
sheet1_cols = ["ATH Değişimi TL (%)", "Geçen Gün", "AVWAP", "AVWAP +4σ", "% Fark VWAP",
               "POC", "VAL", "VAH", "% Fark POC", "% Fark VAL", "VP Bant / ATH Aralığı (%)"]

sheet2_cols = ["Hisse Adı", "Sektör", "Period", "Ortalama Hedef Fiyat", "OHD - USD",
               "Hisse Potansiyeli (Yüzde)", "Hisse Puanı", "YDF Oranı", "Özkaynak Karlılığı",
               "Yıllık Net Kar", "Borç Özkaynak Oranı", "Ödenmiş Sermaye", "Bölünme",
               "Piyasa Değeri", "Peg Rasyosu", "FD/FAVÖK", "ROIC Oranı", "PD/FCF", "Cari Oran",
               "Net Borç/Favök", "F/K Oranı", "PD/DD Oranı", "Hisse Fiyatı"]

st.info("Hisse Temel ve Teknik Değerler Listesi")
df1 = read_google_sheet(sheet1_id, 0, sheet1_cols)
df2 = read_google_sheet(sheet2_id, 0, sheet2_cols)
df = pd.concat([df2, df1], axis=1)

# === AgGrid yapılandırması ===
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
gb.configure_selection("single", use_checkbox=True)
gb.configure_side_bar()

numeric_columns = df.select_dtypes(include="number").columns.tolist()
for col in numeric_columns:
    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2)

# === Hisse Adı sütununa hyperlink ekle ===
gb.configure_column(
    "Hisse Adı",
    cellRenderer="""
        function(params) {
            const symbol = params.value.replace(/"/g, '');
            const url = `https://tr.tradingview.com/chart/hOArWHrE/?symbol=BIST:${symbol}`;
            return `<span style="cursor:pointer;"><a href="${url}" target="_blank" style="text-decoration:none;color:#1f77b4;">${params.value}</a></span>`;
        }
    """
)

grid_options = gb.build()

# === Tablo gösterimi ===
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
