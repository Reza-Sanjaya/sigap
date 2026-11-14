"""
SIGAP KARANG
Peringatan Dini Pemutihan Karang Berbasis Komunitas dan Platform Digital
Jalankan:  streamlit run app.py
"""
import datetime as dt
import html
from string import Template

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="SIGAP KARANG", page_icon="🪸", layout="wide")

# =============================================================== DATA TETAP
# Tiga tingkat peringatan (sama seperti di esai).
LEVELS = {
    "Pantau": dict(warna="#2563eb", rgb=[37, 99, 235], noaa="setara Tidak ada stres / Watch NOAA"),
    "Siaga": dict(warna="#d97706", rgb=[217, 119, 6], noaa="setara Warning NOAA"),
    "Awas": dict(warna="#dc2626", rgb=[220, 38, 38], noaa="setara Alert Level 1 dan 2 NOAA"),
}

CATATAN_AWAS = (
    "Catatan: pada DHW sekitar 12 atau lebih, tutupan karang di Indonesia mulai turun tajam "
    "(Razak dkk., 2026). Angka 12 hanya sebagai catatan, bukan batas mulai Awas."
)
CATATAN_BATAS = "Batas ini akan diperiksa ulang bersama pakar BRIN dan KKP di setiap kawasan."
TEKS_SIMULASI = "Data pada halaman ini adalah simulasi untuk demonstrasi."

TINDAKAN = {
    "Pantau": ["Pemeriksaan rutin.", "Sosialisasi ke operator wisata."],
    "Siaga": [
        "Laporan lebih sering.",
        "Wisatawan diminta tidak menyentuh karang.",
        "Periksa area berjangkar.",
    ],
    "Awas": [
        "Batasi jumlah penyelam dan jangkar di titik rentan.",
        "Hentikan kegiatan yang menambah tekanan (membuang sampah dan limbah).",
    ],
}

# Lokasi contoh. MMM = suhu rata-rata bulanan maksimum (angka ILUSTRASI).
# offset hanya dipakai untuk membuat data simulasi bervariasi antar lokasi.
SITES = pd.DataFrame(
    [
        ("Tejakula (Buleleng, Bali utara)", -8.12, 115.35, 29.2, 0.30),
        ("Nusa Penida", -8.73, 115.54, 28.7, 0.15),
        ("Pesisir Tulungagung", -8.30, 111.90, 28.9, 0.00),
        ("Prigi, Trenggalek", -8.29, 111.73, 28.9, -0.10),
        ("Karimunjawa", -5.80, 110.45, 29.6, 0.20),
        ("Gili Matra, Lombok", -8.35, 116.04, 29.4, 0.10),
        ("Bunaken", 1.62, 124.76, 29.8, -0.25),
        ("Wakatobi", -5.33, 123.58, 29.7, -0.35),
        ("Raja Ampat", -0.50, 130.52, 29.9, -0.45),
        ("Pulau Weh, Aceh", 5.87, 95.32, 29.8, -0.20),
    ],
    columns=["lokasi", "lat", "lon", "MMM", "offset"],
)

# Kode titik pantau -> lokasi
KODE_LOKASI = {
    "TJK-01": "Tejakula (Buleleng, Bali utara)",
    "TJK-02": "Tejakula (Buleleng, Bali utara)",
    "TJK-03": "Tejakula (Buleleng, Bali utara)",
    "NPD-01": "Nusa Penida",
    "NPD-02": "Nusa Penida",
    "TLG-01": "Pesisir Tulungagung",
    "TLG-02": "Pesisir Tulungagung",
    "PRG-01": "Prigi, Trenggalek",
    "KRJ-01": "Karimunjawa",
    "GLM-01": "Gili Matra, Lombok",
    "BNK-01": "Bunaken",
    "WKT-01": "Wakatobi",
    "RJA-01": "Raja Ampat",
    "WEH-01": "Pulau Weh, Aceh",
}

KONDISI = {
    "Normal": "warna karang cerah seperti biasa",
    "Pucat": "warna karang mulai memudar",
    "Memutih": "sebagian besar koloni tampak putih",
}

# =============================================================== LOGIKA
def hitung_dhw(sst_mingguan, mmm):
    """DHW (°C-minggu) = jumlah HotSpot >= 1°C selama 12 minggu terakhir."""
    hotspot = np.array(sst_mingguan, dtype=float) - mmm
    return float(hotspot[hotspot >= 1].sum()), float(hotspot[-1])


def tentukan_level(hotspot, dhw):
    if dhw >= 4:
        return "Awas"  # setara Alert Level 1 (DHW 4) dan 2 (DHW 8)
    if hotspot >= 1:
        return "Siaga"  # setara Warning
    return "Pantau"  # setara Tidak ada stres / Watch


def simulasi(skenario):
    """Data DEMO. Ganti dengan data NOAA Coral Reef Watch untuk versi nyata."""
    rng = np.random.default_rng(7)
    baris = []
    for s in SITES.itertuples():
        naik = np.linspace(-1.2, -0.3 + skenario * 2.2, 12) + s.offset
        sst = s.MMM + naik + rng.normal(0, 0.08, 12)
        dhw, hs = hitung_dhw(sst, s.MMM)
        level = tentukan_level(hs, dhw)
        baris.append(
            dict(lokasi=s.lokasi, lat=s.lat, lon=s.lon, SST=round(float(sst[-1]), 2),
                 HotSpot=round(hs, 2), DHW=round(dhw, 2), level=level,
                 rgb=LEVELS[level]["rgb"], radius=60000)
        )
    return pd.DataFrame(baris)


# =============================================================== TAMPILAN
def palet(gelap):
    if gelap:
        return dict(bg="#0b1820", panel="#13262f", teks="#e6f1f5", redup="#9db6c0",
                    garis="#2c4551", aksen="#1b8fa0", input="#13262f")
    return dict(bg="#ffffff", panel="#f1f7fa", teks="#12333d", redup="#4d6b76",
                garis="#cfe0e6", aksen="#0a7c8c", input="#ffffff")


CSS = Template("""
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:$bg !important;color:$teks}
[data-testid="stHeader"]{background:$bg !important}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:$panel !important}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,.stApp li,.stApp label,.stApp span,.stApp td,.stApp th,
.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricLabel"] *,.stApp [data-testid="stSlider"] div{color:$teks}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] *,.stApp .kecil{color:$redup}
.stApp input,.stApp textarea,.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp [data-baseweb="select"]>div{background:$input !important;color:$teks !important;border-color:$garis !important}
.stApp [data-baseweb="select"] *{color:$teks !important;background-color:$input !important}
.stApp [data-baseweb="select"] svg{fill:$teks}
.stApp [data-testid="stSelectbox"] *{color:$teks !important;background-color:$input !important}
.stApp [data-testid="stSelectbox"] svg{fill:$teks}
.stApp [data-testid="stDateInputField"],.stApp [data-testid="stDateInputField"] *{color:$teks !important;background-color:$input !important}
.stApp [data-testid="stWidgetLabel"],.stApp [data-testid="stWidgetLabel"] *{background-color:transparent !important}
[data-baseweb="calendar"],[data-baseweb="calendar"] *{background-color:$panel !important;color:$teks !important}
[data-baseweb="popover"],[data-baseweb="popover"] ul,[data-baseweb="popover"] li,[data-baseweb="menu"]{background:$panel !important;color:$teks !important}
.stApp [data-testid="stNumberInput"] button{background:$input !important;color:$teks !important;border-color:$garis !important}
.stApp [data-testid="stForm"],.stApp [data-testid="stExpander"]{border-color:$garis !important}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{background:$panel;color:$teks}
.stApp [data-testid="stFileUploaderDropzone"]{background:$input !important}
.stApp [data-testid="stFileUploaderDropzone"] *{color:$teks}
.stApp .stButton>button,.stApp [data-testid="stFormSubmitButton"]>button,.stApp [data-testid="stDownloadButton"]>button,.stApp [data-testid="stFileUploaderDropzone"] button{background:$aksen !important;border:none !important}
.stApp .stButton>button *,.stApp [data-testid="stFormSubmitButton"]>button *,.stApp [data-testid="stDownloadButton"]>button *,.stApp [data-testid="stFileUploaderDropzone"] button *{color:#fff !important}

.stApp .hero{background:linear-gradient(135deg,#023e58,#0a7c8c 60%,#ff7a59);padding:2rem;border-radius:18px;margin-bottom:1rem}
.stApp .hero,.stApp .hero *{color:#fff !important}
.hero h1{margin:0;font-size:2.1rem}
.hero p{margin:.4rem 0 0;font-size:1.05rem}
.stApp .badge{display:inline-block;padding:.2rem .7rem;border-radius:999px;font-weight:600;font-size:.85rem;color:#fff !important}
.card{background:$panel;border-left:6px solid $aksen;padding:.9rem 1.1rem;border-radius:10px;margin-bottom:.6rem}
.card ul{margin:.4rem 0 0;padding-left:1.2rem}
.kecil{font-size:.8rem}
.box{padding:.7rem 1rem;border-radius:10px;margin:.5rem 0;border-left:6px solid}
.box.ok{background:rgba(34,197,94,.15);border-color:#22c55e}
.box.bad{background:rgba(220,38,38,.15);border-color:#dc2626}
.box.info{background:rgba(37,99,235,.13);border-color:#2563eb}
.box.warn{background:rgba(250,204,21,.20);border-color:#d4a900}
.tbl-wrap{overflow-x:auto;margin:.4rem 0 .8rem}
.tbl{width:100%;border-collapse:collapse;font-size:.93rem}
.tbl th{background:$panel;text-align:left}
.tbl th,.tbl td{border:1px solid $garis;padding:.45rem .6rem}
""")


def kotak(teks, jenis="info"):
    st.markdown(f'<div class="box {jenis}">{teks}</div>', unsafe_allow_html=True)


def kotak_simulasi():
    kotak(f"<b>DATA SIMULASI</b> · {TEKS_SIMULASI}", "warn")


def badge(level):
    return f'<span class="badge" style="background:{LEVELS[level]["warna"]}">{level}</span>'


def badge_noaa(level):
    return f'{badge(level)} <span class="kecil">({LEVELS[level]["noaa"]})</span>'


def tabel_html(df, mentah=()):
    kepala = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    isi = ""
    for _, r in df.iterrows():
        sel = "".join(
            f"<td>{r[c] if c in mentah else html.escape(str(r[c]))}</td>" for c in df.columns
        )
        isi += f"<tr>{sel}</tr>"
    st.markdown(
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{kepala}</tr></thead>'
        f"<tbody>{isi}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def tema_grafik(chart, P):
    return (
        chart.configure(background="transparent")
        .configure_axis(labelColor=P["teks"], titleColor=P["teks"], gridColor=P["garis"],
                        domainColor=P["garis"], tickColor=P["garis"])
        .configure_legend(labelColor=P["teks"], titleColor=P["teks"])
        .configure_view(strokeWidth=0)
    )


def grafik_dhw(df, P):
    batas = max(10.0, float(df["DHW"].max()) * 1.15)
    sx = alt.Scale(domain=[0, batas])
    urut = df.sort_values("DHW", ascending=False)["lokasi"].tolist()
    warna = alt.Scale(domain=list(LEVELS), range=[v["warna"] for v in LEVELS.values()])
    dasar = alt.Chart(df).encode(
        y=alt.Y("lokasi:N", sort=urut, title=None, axis=alt.Axis(labelLimit=240))
    )
    batang = dasar.mark_bar().encode(
        x=alt.X("DHW:Q", scale=sx, title="Akumulasi stres panas (DHW, °C-minggu)"),
        color=alt.Color("level:N", scale=warna, legend=alt.Legend(title="Tingkat")),
        tooltip=["lokasi", "level", "DHW"],
    )
    angka = dasar.mark_text(align="left", dx=4, color=P["teks"]).encode(
        x=alt.X("DHW:Q", scale=sx), text=alt.Text("DHW:Q", format=".1f")
    )
    garis = (
        alt.Chart(pd.DataFrame({"x": [4, 8]}))
        .mark_rule(strokeDash=[5, 4], color=P["redup"])
        .encode(x=alt.X("x:Q", scale=sx))
    )
    return tema_grafik(
        alt.layer(batang, angka, garis).properties(height=34 * len(df) + 50), P
    )


def grafik_suhu(sst, mmm, P):
    d = pd.DataFrame({"minggu": list(range(1, 13)), "suhu": [float(v) for v in sst]})
    rendah = min(min(sst), mmm) - 0.5
    tinggi = max(max(sst), mmm + 1) + 0.5
    sy = alt.Scale(domain=[rendah, tinggi])
    sx = alt.Scale(domain=[1, 12])
    garis = alt.Chart(d).mark_line(point=True, color=P["aksen"]).encode(
        x=alt.X("minggu:Q", scale=sx, title="Minggu ke-",
                axis=alt.Axis(values=list(range(1, 13)))),
        y=alt.Y("suhu:Q", scale=sy, title="Suhu laut (°C)"),
        tooltip=["minggu", "suhu"],
    )
    ket_aman, ket_siaga = "Batas aman (MMM)", "Mulai Siaga (MMM + 1 °C)"
    acuan = pd.DataFrame({"y": [mmm, mmm + 1], "ket": [ket_aman, ket_siaga]})
    rule = (
        alt.Chart(acuan)
        .mark_rule(strokeDash=[5, 4])
        .encode(
            y=alt.Y("y:Q", scale=sy),
            color=alt.Color(
                "ket:N",
                scale=alt.Scale(domain=[ket_aman, ket_siaga],
                                range=[LEVELS["Pantau"]["warna"], LEVELS["Siaga"]["warna"]]),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
        )
    )
    return tema_grafik(alt.layer(garis, rule).properties(height=320), P)


# =============================================================== STATE
if "laporan" not in st.session_state:
    contoh = [
        ("2026-11-10", "TJK-03", "Contoh Relawan A", "Pucat", "menunggu verifikasi"),
        ("2026-11-11", "TJK-01", "Contoh Relawan B", "Memutih", "terverifikasi"),
        ("2026-11-12", "TJK-02", "Contoh Relawan C", "Memutih", "menunggu verifikasi"),
        ("2026-11-12", "NPD-01", "Contoh Relawan D", "Normal", "terverifikasi"),
        ("2026-11-13", "TLG-01", "Contoh Relawan E", "Pucat", "menunggu foto"),
    ]
    d = pd.DataFrame(contoh, columns=["tanggal", "kode", "pelapor", "kondisi", "status"])
    d.insert(2, "lokasi", d["kode"].map(KODE_LOKASI))
    st.session_state.laporan = d

# =============================================================== KERANGKA HALAMAN
_, kol_tema = st.columns([4, 1])
gelap = kol_tema.toggle("🌙 Mode gelap", key="mode_gelap")
P = palet(gelap)
st.markdown(f"<style>{CSS.substitute(**P)}</style>", unsafe_allow_html=True)

st.sidebar.title("🪸 SIGAP KARANG")
halaman = st.sidebar.radio(
    "Menu",
    ["Beranda", "Dashboard Peringatan Dini", "Kalkulator DHW", "Lapor Kondisi Karang",
     "Peta", "Protokol Tindakan", "Tentang"],
)
st.sidebar.caption("Data suhu pada prototipe ini adalah simulasi untuk demonstrasi.")

# =============================================================== HALAMAN
if halaman == "Beranda":
    st.markdown(
        '<div class="hero"><h1>El Niño Kuat Datang, Terumbu Karang Belum Siaga</h1>'
        "<p><b>SIGAP KARANG</b>: peringatan dini pemutihan karang berbasis komunitas "
        "dan platform digital.</p></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="card"><b>1. Pantau</b><br>Suhu laut dan indikator stres panas.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="card"><b>2. Laporkan</b><br>Nelayan, penyelam, dan pemuda pesisir mengirim laporan lapangan.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="card"><b>3. Bertindak</b><br>Protokol tindakan tiga tingkat: Pantau, Siaga, Awas.</div>', unsafe_allow_html=True)
    st.subheader("Mengapa penting?")
    st.write(
        "Suhu laut yang tinggi dalam waktu lama membuat karang melepas alga simbionnya "
        "(zooxanthellae) sehingga memutih dan bisa mati. Data satelit sudah ada, tetapi "
        "sering belum sampai ke masyarakat pesisir. SIGAP KARANG menghubungkan data satelit "
        "dengan laporan komunitas agar tindakan dapat dimulai sebelum kerusakan meluas."
    )
    st.subheader("SIGAP")
    tabel_html(pd.DataFrame({
        "Huruf": ["S", "I", "G", "A", "P"],
        "Arti": ["Sensor suhu dan satelit", "Informasi komunitas", "Gerak cepat (peringatan dini)",
                 "Aksi perlindungan karang", "Pulih dan evaluasi"],
    }))

elif halaman == "Dashboard Peringatan Dini":
    st.header("Dashboard Peringatan Dini")
    kotak_simulasi()
    skenario = st.slider(
        "Skenario kekuatan El Niño (0 = normal, 1 = kuat, 2 = ekstrem)", 0.0, 2.0, 0.8, 0.1
    )
    df = simulasi(skenario)
    m1, m2, m3 = st.columns(3)
    m1.metric("Lokasi dipantau", len(df))
    m2.metric("Lokasi berstatus Awas", int((df.level == "Awas").sum()))
    m3.metric("DHW tertinggi (°C-minggu)", f"{df.DHW.max():.1f}")

    urut = df.sort_values("DHW", ascending=False)
    tabel_html(
        pd.DataFrame({
            "Lokasi": urut.lokasi,
            "Tingkat": urut.level.map(badge),
            "Suhu laut (SST)": urut.SST.map(lambda v: f"{v:.1f} °C"),
            "Selisih suhu (HotSpot)": urut.HotSpot.map(lambda v: f"{v:.1f} °C"),
            "Akumulasi stres panas (DHW)": urut.DHW.map(lambda v: f"{v:.1f}"),
        }),
        mentah=("Tingkat",),
    )
    st.subheader("Akumulasi stres panas per lokasi")
    st.altair_chart(grafik_dhw(df, P), theme=None)
    st.caption("Garis putus-putus: DHW 4 (mulai Awas) dan DHW 8.")

    st.subheader("Cara membaca tingkat")
    tabel_html(
        pd.DataFrame({
            "Tingkat": [badge(k) for k in LEVELS],
            "Artinya (skala NOAA)": [
                "Tidak ada stres, atau Watch",
                "Warning (HotSpot 1 atau lebih)",
                "Alert Level 1 (DHW 4 atau lebih) dan Alert Level 2 (DHW 8 atau lebih)",
            ],
        }),
        mentah=("Tingkat",),
    )
    st.markdown(f'<div class="kecil">{CATATAN_AWAS}</div>', unsafe_allow_html=True)

elif halaman == "Kalkulator DHW":
    st.header("Kalkulator Akumulasi Stres Panas (DHW)")
    kotak_simulasi()
    lokasi = st.selectbox("Lokasi", SITES.lokasi)
    mmm0 = float(SITES.loc[SITES.lokasi == lokasi, "MMM"].iloc[0])
    mmm = st.number_input(
        "Suhu aman maksimum bulanan (MMM, °C)", value=mmm0, step=0.1, format="%.1f",
        key=f"mmm_{lokasi}",
    )
    st.write("Isi suhu laut mingguan selama 12 minggu terakhir (minggu ke-12 adalah yang terbaru).")
    awal = np.round(np.linspace(mmm0 - 1.0, mmm0 + 1.4, 12), 1)
    sst = []
    for baris in range(3):
        for j, kol in enumerate(st.columns(4)):
            i = baris * 4 + j
            sst.append(kol.number_input(
                f"Minggu {i + 1}", 20.0, 36.0, float(awal[i]), 0.1, format="%.1f",
                key=f"sst_{lokasi}_{i}",
            ))
    dhw, hs = hitung_dhw(sst, mmm)
    level = tentukan_level(hs, dhw)
    k1, k2 = st.columns(2)
    k1.metric("Akumulasi stres panas (DHW)", f"{dhw:.2f} °C-minggu")
    k2.metric("Selisih suhu minggu ini (HotSpot)", f"{hs:.2f} °C")
    st.markdown(f"Tingkat: {badge_noaa(level)}", unsafe_allow_html=True)
    kotak(" ".join(TINDAKAN[level]), "info")
    if level == "Awas":
        st.markdown(f'<div class="kecil">{CATATAN_AWAS}</div>', unsafe_allow_html=True)
    st.altair_chart(grafik_suhu(sst, mmm, P), theme=None)

elif halaman == "Lapor Kondisi Karang":
    st.header("Lapor Kondisi Karang")
    kotak_simulasi()
    with st.form("form_lapor", clear_on_submit=True):
        a, b = st.columns(2)
        pelapor = a.text_input("Nama pelapor / kelompok")
        kode = b.selectbox(
            "Kode titik pantau", list(KODE_LOKASI), index=2,
            format_func=lambda k: f"{k} · {KODE_LOKASI[k]}",
        )
        tgl = a.date_input("Tanggal", dt.date.today())
        kondisi = b.radio("Kondisi karang", list(KONDISI), horizontal=True)
        b.caption(" · ".join(f"{k}: {v}" for k, v in KONDISI.items()))
        suhu = a.number_input("Suhu air (°C)", 20.0, 36.0, 29.0, 0.1)
        dalam = b.number_input("Kedalaman (m)", 1, 40, 5)
        foto = st.file_uploader(
            "Foto karang (dianjurkan)", type=["jpg", "jpeg", "png"],
            help="Tanpa foto, status laporan menjadi 'menunggu foto'.",
        )
        kirim = st.form_submit_button("Kirim laporan")
    if kirim:
        status = "menunggu verifikasi" if foto is not None else "menunggu foto"
        baru = pd.DataFrame(
            [[str(tgl), kode, KODE_LOKASI[kode], pelapor or "Anonim", kondisi, status]],
            columns=st.session_state.laporan.columns,
        )
        st.session_state.laporan = pd.concat([st.session_state.laporan, baru], ignore_index=True)
        kotak(f"Laporan terkirim. Status: <b>{status}</b>.", "ok")
        if foto is None:
            st.caption("Tambahkan foto agar laporan dapat diperiksa.")

    with st.expander("Daftar kode titik pantau"):
        tabel_html(pd.DataFrame(
            [(k, v) for k, v in KODE_LOKASI.items()], columns=["Kode titik", "Lokasi"]
        ))

    lap = st.session_state.laporan
    st.subheader("Laporan masuk")
    tabel_html(lap.rename(columns={
        "tanggal": "Tanggal", "kode": "Kode titik", "lokasi": "Lokasi",
        "pelapor": "Pelapor", "kondisi": "Kondisi", "status": "Status",
    }))
    memutih = lap[lap.kondisi == "Memutih"].groupby("lokasi").size()
    for lok, n in memutih[memutih >= 2].items():
        kotak(f"<b>Peringatan komunitas:</b> {n} laporan karang memutih di {html.escape(lok)}. "
              "Segera periksa dan verifikasi.", "bad")
    st.download_button("Unduh laporan (CSV)", lap.to_csv(index=False).encode("utf-8"),
                       "laporan_karang.csv", "text/csv")

elif halaman == "Peta":
    st.header("Peta Tingkat Peringatan")
    kotak_simulasi()
    skenario = st.slider("Skenario kekuatan El Niño (0 = normal, 1 = kuat, 2 = ekstrem)", 0.0, 2.0, 0.8, 0.1, key="peta")
    df = simulasi(skenario)
    layer = pdk.Layer(
        "ScatterplotLayer", data=df, get_position="[lon, lat]", get_fill_color="rgb",
        get_radius="radius", radius_min_pixels=7, radius_max_pixels=18, pickable=True,
        stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=-3.0, longitude=116.0, zoom=3.2),
        map_style="dark" if gelap else "light",
        tooltip={"text": "{lokasi}\nTingkat: {level}\nDHW: {DHW}"},
    )
    st.pydeck_chart(deck)
    st.caption("Warna titik mengikuti tingkat peringatan.")
    st.markdown("<br>".join(badge_noaa(k) for k in LEVELS), unsafe_allow_html=True)

elif halaman == "Protokol Tindakan":
    st.header("Protokol Tindakan per Tingkat Peringatan")
    for level, daftar in TINDAKAN.items():
        butir = "".join(f"<li>{t}</li>" for t in daftar)
        tambahan = f'<div class="kecil" style="margin-top:.5rem">{CATATAN_AWAS}</div>' if level == "Awas" else ""
        st.markdown(
            f'<div class="card">{badge_noaa(level)}<ul>{butir}</ul>{tambahan}</div>',
            unsafe_allow_html=True,
        )
    st.subheader("Peran komunitas")
    st.markdown(
        "- **Nelayan dan operator wisata**: lapor perubahan warna karang dan suhu air.\n"
        "- **Pemuda dan sekolah**: survei visual sederhana dan edukasi.\n"
        "- **Pemerintah desa dan pengelola kawasan**: keputusan pengaturan kegiatan di kawasan.\n"
        "- **Peneliti dan kampus**: validasi data dan pelatihan relawan."
    )

else:
    st.header("Tentang")
    st.write("SIGAP KARANG adalah prototipe platform peringatan dini pemutihan karang "
             "yang menggabungkan indikator suhu laut dan laporan komunitas.")
    kotak(f"<b>DATA SIMULASI</b> · Data suhu di prototipe ini disimulasikan untuk demonstrasi. "
          "Versi nyata memakai data NOAA Coral Reef Watch (HotSpot dan DHW) dan status "
          "El Niño dari BMKG.", "warn")
    kotak(CATATAN_BATAS, "info")
    st.write("Pengembangan lanjutan: integrasi data NOAA Coral Reef Watch, penyimpanan laporan "
             "ke basis data, dan klasifikasi foto karang otomatis.")
