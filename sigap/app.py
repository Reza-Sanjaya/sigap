"""
SIGAP KARANG
Peringatan Dini Pemutihan Karang Berbasis Komunitas dan Platform Digital
Jalankan:  streamlit run app.py
"""
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SIGAP KARANG", page_icon="🪸", layout="wide")

# ---------------------------------------------------------------- TAMPILAN
st.markdown(
    """
<style>
.hero{background:linear-gradient(135deg,#023e58,#0a7c8c 60%,#ff7a59);
      padding:2rem 2rem;border-radius:18px;color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2.2rem;color:white}
.hero p{margin:.4rem 0 0;font-size:1.05rem;opacity:.95}
.badge{display:inline-block;padding:.25rem .7rem;border-radius:999px;
       font-weight:600;color:white;font-size:.85rem}
.card{background:#f4f9fb;border-left:6px solid #0a7c8c;padding:.9rem 1.1rem;
      border-radius:10px;margin-bottom:.6rem;color:#12333d}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- DATA & LOGIKA
# Lokasi contoh. MMM = suhu rata-rata bulanan maksimum (angka ILUSTRASI).
SITES = pd.DataFrame(
    [
        ("Pesisir Tulungagung", -8.30, 111.90, 28.9),
        ("Prigi, Trenggalek", -8.29, 111.73, 28.9),
        ("Karimunjawa", -5.80, 110.45, 29.6),
        ("Gili Matra, Lombok", -8.35, 116.04, 29.4),
        ("Bunaken", 1.62, 124.76, 29.8),
        ("Wakatobi", -5.33, 123.58, 29.7),
        ("Raja Ampat", -0.50, 130.52, 29.9),
        ("Pulau Weh, Aceh", 5.87, 95.32, 29.8),
    ],
    columns=["lokasi", "lat", "lon", "MMM"],
)

LEVELS = {
    "Tidak ada stres": "#3b82f6",
    "Watch": "#d4a900",
    "Warning": "#f97316",
    "Alert Level 1": "#ef4444",
    "Alert Level 2": "#991b1b",
}

ACTIONS = {
    "Tidak ada stres": "Pemantauan rutin. Latih relawan dan perbarui data dasar kondisi karang.",
    "Watch": "Siaga: pantau suhu mingguan, ingatkan nelayan dan operator wisata.",
    "Warning": "Intai: survei visual mingguan, kurangi tekanan lokal (jangkar, sampah, limbah).",
    "Alert Level 1": "Gerak: pemutihan mungkin terjadi. Batasi aktivitas selam dan snorkeling, lapor ke otoritas.",
    "Alert Level 2": "Aksi: pemutihan parah dan kematian karang mungkin terjadi. Tutup zona rentan, dokumentasi massal.",
}


def hitung_dhw(sst_mingguan, mmm):
    """DHW (°C-minggu) = jumlah HotSpot >= 1°C selama 12 minggu terakhir."""
    hotspot = np.array(sst_mingguan, dtype=float) - mmm
    return float(hotspot[hotspot >= 1].sum()), float(hotspot[-1])


def tentukan_level(hotspot, dhw):
    if dhw >= 8:
        return "Alert Level 2"
    if dhw >= 4:
        return "Alert Level 1"
    if hotspot >= 1:
        return "Warning"
    if hotspot > 0:
        return "Watch"
    return "Tidak ada stres"


def badge(level):
    return f'<span class="badge" style="background:{LEVELS[level]}">{level}</span>'


def simulasi(skenario, seed=7):
    """Data DEMO. Ganti dengan data NOAA Coral Reef Watch untuk versi nyata."""
    rng = np.random.default_rng(seed)
    baris = []
    for _, s in SITES.iterrows():
        naik = np.linspace(-1.4, -0.2 + skenario * 1.3, 12)
        sst = s.MMM + naik + rng.normal(0, 0.15, 12)
        dhw, hs = hitung_dhw(sst, s.MMM)
        level = tentukan_level(hs, dhw)
        baris.append(
            dict(lokasi=s.lokasi, lat=s.lat, lon=s.lon, SST=round(sst[-1], 2),
                 HotSpot=round(hs, 2), DHW=round(dhw, 2), level=level,
                 color=LEVELS[level], size=9000)
        )
    return pd.DataFrame(baris)


def status_laporan(persen):
    if persen < 10:
        return "Normal"
    if persen < 30:
        return "Mulai memutih"
    if persen < 50:
        return "Pemutihan parah"
    return "Kritis"


if "laporan" not in st.session_state:
    st.session_state.laporan = pd.DataFrame(
        [
            ("2026-11-10", "Pesisir Tulungagung", "Contoh Relawan A", 12, 29.4, 4),
            ("2026-11-11", "Pesisir Tulungagung", "Contoh Relawan B", 35, 29.6, 5),
            ("2026-11-12", "Karimunjawa", "Contoh Relawan C", 8, 30.1, 3),
        ],
        columns=["tanggal", "lokasi", "pelapor", "persen_memutih", "suhu_air", "kedalaman_m"],
    )

# ---------------------------------------------------------------- NAVIGASI
st.sidebar.title("🪸 SIGAP KARANG")
halaman = st.sidebar.radio(
    "Menu",
    ["Beranda", "Dashboard Peringatan Dini", "Kalkulator DHW", "Lapor Karang (Komunitas)",
     "Peta", "Protokol SIGAP", "Tentang"],
)
st.sidebar.caption("Data suhu pada prototipe ini adalah simulasi untuk demonstrasi.")

# ---------------------------------------------------------------- HALAMAN
if halaman == "Beranda":
    st.markdown(
        """<div class="hero"><h1>El Niño Kuat Datang, Terumbu Karang Belum Siaga</h1>
        <p><b>SIGAP KARANG</b>: peringatan dini pemutihan karang berbasis komunitas
        dan platform digital.</p></div>""",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="card"><b>1. Pantau</b><br>Suhu laut dan indikator stres panas (HotSpot, DHW).</div>', unsafe_allow_html=True)
    c2.markdown('<div class="card"><b>2. Laporkan</b><br>Nelayan, penyelam, dan pemuda pesisir mengirim laporan lapangan.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="card"><b>3. Bertindak</b><br>Protokol aksi otomatis sesuai tingkat peringatan.</div>', unsafe_allow_html=True)
    st.subheader("Mengapa penting?")
    st.write(
        "Suhu laut yang tinggi dalam waktu lama membuat karang melepas alga simbionnya "
        "(zooxanthellae) sehingga memutih dan bisa mati. Data satelit sudah ada, tetapi "
        "sering belum sampai ke masyarakat pesisir. SIGAP KARANG menghubungkan data satelit "
        "dengan laporan komunitas agar tindakan dapat dimulai sebelum kerusakan meluas."
    )
    st.subheader("SIGAP")
    st.table(pd.DataFrame({
        "Huruf": ["S", "I", "G", "A", "P"],
        "Arti": ["Sensor suhu dan satelit", "Informasi komunitas", "Gerak cepat (peringatan dini)",
                 "Aksi perlindungan karang", "Pulih dan evaluasi"],
    }).set_index("Huruf"))

elif halaman == "Dashboard Peringatan Dini":
    st.header("Dashboard Peringatan Dini")
    skenario = st.slider("Skenario kekuatan El Niño (0 = normal, 1 = kuat, 2 = ekstrem)", 0.0, 2.0, 1.0, 0.1)
    df = simulasi(skenario)
    jumlah_alert = int(df.level.isin(["Alert Level 1", "Alert Level 2"]).sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Lokasi dipantau", len(df))
    m2.metric("Lokasi status Alert", jumlah_alert)
    m3.metric("DHW tertinggi (°C-minggu)", df.DHW.max())
    for _, r in df.sort_values("DHW", ascending=False).iterrows():
        st.markdown(
            f'**{r.lokasi}** {badge(r.level)} &nbsp; SST {r.SST}°C · HotSpot {r.HotSpot} · DHW {r.DHW}',
            unsafe_allow_html=True,
        )
    st.subheader("DHW per lokasi")
    st.bar_chart(df.set_index("lokasi")["DHW"])
    st.info("Aturan level (mengikuti skala NOAA Coral Reef Watch): Watch = HotSpot > 0; "
            "Warning = HotSpot ≥ 1; Alert Level 1 = DHW ≥ 4; Alert Level 2 = DHW ≥ 8.")

elif halaman == "Kalkulator DHW":
    st.header("Kalkulator Degree Heating Weeks (DHW)")
    st.write("Isi suhu laut mingguan selama 12 minggu terakhir. Anda bisa mengedit angkanya.")
    lokasi = st.selectbox("Lokasi", SITES.lokasi)
    mmm = float(SITES.loc[SITES.lokasi == lokasi, "MMM"].iloc[0])
    mmm = st.number_input("MMM (suhu rata-rata bulanan maksimum, °C)", value=mmm, step=0.1)
    awal = pd.DataFrame({"minggu": range(1, 13), "SST": np.round(np.linspace(mmm - 1, mmm + 1.3, 12), 2)})
    data = st.data_editor(awal, hide_index=True)
    dhw, hs = hitung_dhw(data["SST"], mmm)
    level = tentukan_level(hs, dhw)
    st.metric("DHW", f"{dhw:.2f} °C-minggu")
    st.markdown(f"Status: {badge(level)}", unsafe_allow_html=True)
    st.success(ACTIONS[level])
    st.line_chart(data.set_index("minggu")["SST"])

elif halaman == "Lapor Karang (Komunitas)":
    st.header("Lapor Kondisi Karang")
    with st.form("form_lapor", clear_on_submit=True):
        a, b = st.columns(2)
        pelapor = a.text_input("Nama pelapor / kelompok")
        lokasi = b.selectbox("Lokasi", SITES.lokasi)
        tgl = a.date_input("Tanggal", dt.date.today())
        persen = b.slider("Perkiraan karang memutih (%)", 0, 100, 10)
        suhu = a.number_input("Suhu air (°C)", 20.0, 36.0, 29.0, 0.1)
        dalam = b.number_input("Kedalaman (m)", 1, 40, 5)
        st.file_uploader("Foto (opsional)", type=["jpg", "jpeg", "png"])
        kirim = st.form_submit_button("Kirim laporan")
    if kirim:
        baru = pd.DataFrame([[str(tgl), lokasi, pelapor or "Anonim", persen, suhu, dalam]],
                            columns=st.session_state.laporan.columns)
        st.session_state.laporan = pd.concat([st.session_state.laporan, baru], ignore_index=True)
        st.success(f"Laporan terkirim. Status: {status_laporan(persen)}")

    lap = st.session_state.laporan.copy()
    lap["status"] = lap.persen_memutih.apply(status_laporan)
    st.subheader("Laporan masuk")
    st.dataframe(lap)
    parah = lap[lap.persen_memutih >= 30].groupby("lokasi").size()
    for lok, n in parah[parah >= 2].items():
        st.error(f"Peringatan komunitas: {n} laporan pemutihan ≥ 30% di {lok}.")
    st.download_button("Unduh laporan (CSV)", lap.to_csv(index=False).encode("utf-8"), "laporan_karang.csv")

elif halaman == "Peta":
    st.header("Peta Status Peringatan")
    skenario = st.slider("Skenario El Niño", 0.0, 2.0, 1.0, 0.1, key="peta")
    df = simulasi(skenario)
    st.map(df, latitude="lat", longitude="lon", color="color", size="size")
    st.caption("Warna titik mengikuti tingkat peringatan.")
    st.markdown(" ".join(badge(k) for k in LEVELS), unsafe_allow_html=True)

elif halaman == "Protokol SIGAP":
    st.header("Protokol Tindakan per Tingkat Peringatan")
    for level, teks in ACTIONS.items():
        st.markdown(f'<div class="card">{badge(level)}<br>{teks}</div>', unsafe_allow_html=True)
    st.subheader("Peran komunitas")
    st.write("- **Nelayan dan operator wisata**: lapor perubahan warna karang dan suhu air.\n"
             "- **Pemuda dan sekolah**: survei visual sederhana dan edukasi.\n"
             "- **Pemerintah desa dan pengelola kawasan**: keputusan pembatasan aktivitas.\n"
             "- **Peneliti dan kampus**: validasi data dan pelatihan relawan.")

else:
    st.header("Tentang")
    st.write("SIGAP KARANG adalah prototipe platform peringatan dini pemutihan karang "
             "yang menggabungkan indikator suhu laut dan laporan komunitas.")
    st.warning("Data suhu di prototipe ini disimulasikan. Untuk versi nyata gunakan data "
               "NOAA Coral Reef Watch (HotSpot, DHW) dan data BMKG untuk status El Niño.")
    st.write("Pengembangan lanjutan: integrasi data NOAA CRW, penyimpanan laporan ke Google Sheets "
             "atau database, notifikasi WhatsApp/Telegram, dan klasifikasi foto karang otomatis.")
