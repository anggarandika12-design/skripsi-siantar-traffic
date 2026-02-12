import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Crowdsourcing Pematangsiantar", layout="wide")

# --- INISIALISASI STATE ---
# Menyimpan koordinat klik agar tidak hilang saat aplikasi refresh
if 'asal' not in st.session_state:
    st.session_state.asal = None
if 'tujuan' not in st.session_state:
    st.session_state.tujuan = None

# --- FUNGSI KIRIM DATA ---
def simpan_ke_gsheets(asal, tujuan):
    url_script = "https://script.google.com/macros/s/AKfycbz6C_aEz4otiQbReLK7gueL74Lznl6-K0A3fLy3VGzVNCOCAH4UhYms4iFV0sXXnTU5/exec"
    waktu_wib = datetime.now() + timedelta(hours=7)
    
    payload = {
        "waktu": waktu_wib.strftime("%Y-%m-%d %H:%M:%S"),
        "asal": f"{asal[0]:.5f}, {asal[1]:.5f}", # Simpan koordinat Lat, Lng
        "tujuan": f"{tujuan[0]:.5f}, {tujuan[1]:.5f}",
        "status": "Dilaporkan via Peta",
        "jam": waktu_wib.strftime("%H:%M")
    }
    
    try:
        response = requests.post(url_script, json=payload)
        return "Sukses" in response.text
    except:
        return False

# --- UI APLIKASI ---
st.title("📍 Klik Peta untuk Lapor Kemacetan")
st.write("Instruksi: **Klik 1** untuk Lokasi Sekarang, **Klik 2** untuk Tujuan.")

# Tombol Reset
if st.button("🔄 Reset Pilihan"):
    st.session_state.asal = None
    st.session_state.tujuan = None
    st.rerun()

# --- PETA INTERAKTIF ---
# Fokus di Pematangsiantar
m = folium.Map(location=[2.9560, 99.0600], zoom_start=14)

# Tambahkan Marker jika sudah diklik
if st.session_state.asal:
    folium.Marker(st.session_state.asal, popup="Asal (1)", icon=folium.Icon(color='green')).add_to(m)
if st.session_state.tujuan:
    folium.Marker(st.session_state.tujuan, popup="Tujuan (2)", icon=folium.Icon(color='red')).add_to(m)
    # Gambar garis penghubung
    folium.PolyLine([st.session_state.asal, st.session_state.tujuan], color="blue", weight=3).add_to(m)

# Tangkap input klik dari peta
output = st_folium(m, width=1300, height=500)

# Logika menangkap koordinat klik
if output['last_clicked']:
    clicked_coords = (output['last_clicked']['lat'], output['last_clicked']['lng'])
    
    if st.session_state.asal is None:
        st.session_state.asal = clicked_coords
        st.rerun()
    elif st.session_state.tujuan is None and clicked_coords != st.session_state.asal:
        st.session_state.tujuan = clicked_coords
        st.rerun()

# --- PROSES PENGIRIMAN ---
if st.session_state.asal and st.session_state.tujuan:
    st.success(f"📍 Rute Terpilih: {st.session_state.asal} ke {st.session_state.tujuan}")
    
    if st.button("🚀 Kirim Laporan Rute Ini"):
        with st.spinner('Mengirim ke Google Sheets...'):
            if simpan_ke_gsheets(st.session_state.asal, st.session_state.tujuan):
                st.balloons()
                st.success("✅ Koordinat rute berhasil terkirim!")
                # Reset setelah sukses
                st.session_state.asal = None
                st.session_state.tujuan = None
            else:
                st.error("❌ Gagal mengirim.")

st.info("Koordinat yang dikirim ke Google Sheets berupa Latitude dan Longitude.")
