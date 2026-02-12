import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection  

# Masukkan link Google Sheet kamu yang sudah di-set "Editor" oleh "Anyone with link"
url_gsheet = "https://docs.google.com/spreadsheets/d/1raP5WltsJnn4U7-Ydr3ubo2EAaYBB05wSr3mENr87jI"

# Inisialisasi koneksi
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Deteksi Kemacetan", layout="wide")

# --- 2. FUNGSI TEKNIS ---

def ambil_nama_tempat(coords):
    """Mengubah koordinat GPS menjadi nama jalan (Reverse Geocoding)"""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={coords[0]}&lon={coords[1]}&format=json"
    headers = {'User-Agent': 'SkripsiApp/1.0'}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('display_name', 'Lokasi tidak dikenal').split(',')[0]
    except:
        return f"Lat: {coords[0]:.4f}, Lon: {coords[1]:.4f}"

def dapatkan_rute_jalan(start, end):
    """Mencari jalur mengikuti lekukan jalan asli"""
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    try:
        res = requests.get(url).json()
        return [[p[1], p[0]] for p in res['routes'][0]['geometry']['coordinates']]
    except:
        return [start, end]
import requests # Pastikan baris ini ada di paling atas file app.py kamu!

def simpan_ke_gsheets(asal, tujuan, status, jam):
    # GANTI URL di bawah ini dengan URL "Aplikasi Web" yang kamu dapat dari Apps Script
    url_script = "https://script.google.com/macros/s/AKfycbygQ0eLqTYkztWAFnmFQkiGEE8wDSHYJ4Uooxz2m_ZJ-ovEkhGiHgVFA7V0v35ZDMqy/exec"
    
    payload = {
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asal": asal,
        "tujuan": tujuan,
        "status": status,
        "jam": jam
    }
    
    try:
        # Mengirim data ke Google Sheets melalui Apps Script
        response = requests.post(url_script, json=payload)
        if "Sukses" in response.text:
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# --- 3. SESSION STATE (PENYIMPANAN DATA) ---
if 'clicks' not in st.session_state:
    st.session_state.clicks = []
if 'nama_lokasi' not in st.session_state:
    st.session_state.nama_lokasi = []

# --- 4. SIDEBAR: KONTROL & CROWDSOURCING ---
st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.markdown("---")

# Simulasi Input Jam
jam_simulasi = st.sidebar.slider("Simulasi Waktu (Jam):", 0, 23, datetime.now().hour)

# Logika Deteksi Berdasarkan Crowdsourcing
if (7 <= jam_simulasi <= 8):
    status, warna, info_crowd = "MACET", "red", "Volume GPS Tinggi (Jam Sibuk)"
elif (12 <= jam_simulasi <= 14) or (17 <= jam_simulasi <= 19):
    status, warna, info_crowd = "PADAT", "orange", "Volume GPS Meningkat (Aktivitas Kota)"
else:
    status, warna, info_crowd = "LANCAR", "green", "Volume GPS Rendah (Arus Stabil)"

st.sidebar.subheader("Analisis Crowdsourcing")
st.sidebar.write(f"**Data Status:** {info_crowd}")
st.sidebar.metric("Status Jalur", status)

# --- 5. TAMPILAN UTAMA ---
st.markdown("<h1 style='text-align: center;'>Sistem Deteksi Kemacetan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Integrasi Data Crowdsourcing GPS Kendaraan & Machine Learning</p>", unsafe_allow_html=True)
st.markdown("---")

if st.button("🔄 Reset Plot GPS"):
    st.session_state.clicks = []
    st.session_state.nama_lokasi = []
    st.rerun()

col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown("### 🗺️ Visualisasi Jalur GPS")
    # Inisialisasi Peta
    m = folium.Map(location=[2.9600, 99.0600], zoom_start=14)

    # Menampilkan Marker dari Klik
    for i, p in enumerate(st.session_state.clicks):
        lbl = "Origin" if i == 0 else "Destination"
        clr = "blue" if i == 0 else "red"
        folium.Marker(p, popup=st.session_state.nama_lokasi[i], icon=folium.Icon(color=clr, icon='info-sign')).add_to(m)

    # Menampilkan Rute Berdasarkan Analisis
    if len(st.session_state.clicks) == 2:
        rute = dapatkan_rute_jalan(st.session_state.clicks[0], st.session_state.clicks[1])
        folium.PolyLine(rute, color=warna, weight=8, opacity=0.8, tooltip=f"Status: {status}").add_to(m)

    # Tangkap Klik Peta
    out = st_folium(m, width=850, height=480, key="peta_skripsi", returned_objects=["last_clicked"])

    if out and out["last_clicked"]:
        pos = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
        if len(st.session_state.clicks) < 2:
            if not st.session_state.clicks or pos != st.session_state.clicks[-1]:
                with st.spinner("Sinkronisasi Lokasi GPS..."):
                    nama = ambil_nama_tempat(pos)
                    st.session_state.clicks.append(pos)
                    st.session_state.nama_lokasi.append(nama)
                st.rerun()

with col2:
    st.subheader("📋 Informasi Crowdsourcing")
    if len(st.session_state.nama_lokasi) >= 1:
        st.write(f"📍 **Origin GPS:**\n{st.session_state.nama_lokasi[0]}")
    if len(st.session_state.nama_lokasi) == 2:
        st.write(f"🏁 **Destination GPS:**\n{st.session_state.nama_lokasi[1]}")
        st.divider()
        st.write(f"**Hasil Deteksi Jam {jam_simulasi:02d}:00**")
        st.subheader(f":{warna}[{status}]")
        if st.button("🚀 Kirim Laporan Crowdsourcing"):
                sukses = simpan_ke_gsheets(
                st.session_state.nama_lokasi[0],
                st.session_state.nama_lokasi[1],
                status,
                jam_simulasi
            )
                if sukses:
                    st.success("Laporan terkirim ke database!")
    else:
        st.info("Klik 2 titik lokasi di peta untuk memproses rute GPS.")
        st.caption(f"Keterangan: {info_crowd}") 

st.markdown("---")
st.caption("Pematangsiantar - Sistem Deteksi Kemacetan Berbasis Crowdsourcing")
