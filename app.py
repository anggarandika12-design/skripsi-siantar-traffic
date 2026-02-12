import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Simulasi Crowdsourcing Kemacetan", layout="wide")

# --- FUNGSI KIRIM DATA KE GOOGLE SHEETS ---
def simpan_ke_gsheets(asal, tujuan, status, jam):
    # URL Web App dari Apps Script kamu
    url_script = "https://script.google.com/macros/s/AKfycbz6C_aEz4otiQbReLK7gueL74Lznl6-K0A3fLy3VGzVNCOCAH4UhYms4iFV0sXXnTU5/exec"
    
    # Waktu standar (tanpa penambahan +7 jam)
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "waktu": waktu_sekarang,
        "asal": asal,
        "tujuan": tujuan,
        "status": status,
        "jam": jam
    }
    
    try:
        response = requests.post(url_script, json=payload)
        if "Sukses" in response.text:
            return True
        return False
    except Exception as e:
        return False

# --- UI APLIKASI ---
st.title("🚗 Sistem Crowdsourcing Pelaporan Kemacetan")
st.write("Gunakan formulir di bawah untuk melaporkan kondisi lalu lintas.")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Peta Wilayah")
    # Fokus koordinat Pematangsiantar
    m = folium.Map(location=[2.9560, 99.0600], zoom_start=14)
    st_folium(m, width=700, height=450)

with col2:
    st.subheader("Formulir Laporan")
    titik_asal = st.text_input("Titik Asal", placeholder="Contoh: Jl. Merdeka")
    titik_tujuan = st.text_input("Titik Tujuan", placeholder="Contoh: Jl. Sutomo")
    status_macet = st.selectbox("Status Kemacetan", ["Lancar", "Padat Merayap", "Macet Total"])
    jam_simulasi = st.time_input("Jam Simulasi")

    if st.button("🚀 Kirim Laporan Crowdsourcing"):
        if titik_asal and titik_tujuan:
            with st.spinner('Sedang mengirim data...'):
                berhasil = simpan_ke_gsheets(
                    titik_asal, 
                    titik_tujuan, 
                    status_macet, 
                    str(jam_simulasi)
                )
                
                if berhasil:
                    st.success("✅ Data berhasil masuk ke Google Sheets!")
                    st.balloons()
                else:
                    st.error("❌ Gagal mengirim. Cek koneksi Apps Script.")
        else:
            st.warning("⚠️ Mohon isi titik asal dan tujuan terlebih dahulu.")

# --- FOOTER ---
st.markdown("---")
st.caption("Aplikasi Skripsi - Simulasi Crowdsourcing Lalu Lintas")
