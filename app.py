import streamlit as st
import os
import io
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==========================================
# 0. KONFIGURASI HALAMAN UTAMA (HANYA BOLEH 1 KALI)
# ==========================================
st.set_page_config(
    page_title="Kurnia Sanusi Farm", 
    page_icon="LogoLaporan.png",
    layout="wide"
)

# KONEKSI DATABASE SQLITE
conn = sqlite3.connect("data_telur.db", check_same_thread=False)

# ==========================================
# 1 & 2. HALAMAN LOGIN NATIVE (STABIL & AMAN)
# ==========================================

# Inisialisasi status login di session state jika belum ada
if "sudah_login" not in st.session_state:
    st.session_state["sudah_login"] = False
if "nama_user" not in st.session_state:
    st.session_state["nama_user"] = ""

# JIKA BELUM LOGIN, TAMPILKAN FORM LOGIN UTAMA
if not st.session_state["sudah_login"]:
    # Membuat box form login di tengah halaman
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🥚 Kurnia Sanusi Farm</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Silakan masuk untuk mengakses sistem rekap</p>", unsafe_allow_html=True)
        
        with st.form("form_login_kandang"):
            input_user = st.text_input("Username", placeholder="Masukkan username Anda")
            input_pass = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
            tombol_masuk = st.form_submit_button("Masuk ke Sistem", use_container_width=True)
            
            if tombol_masuk:
                # VALIDASI DATA AKSES SECARA LANGSUNG
                if input_user == "KSF" and input_pass == "KSF30":
                    st.session_state["sudah_login"] = True
                    st.session_state["nama_user"] = "Kurnia Sanusi"
                    st.success("Login Berhasil! Memuat Dashboard...")
                    st.rerun()
                else:
                    st.error("❌ Username atau Password salah! Periksa kembali input Anda.")
        
        st.info("💡 Petunjuk Akses:\n- Hubungi admin jika lupa data akses akun.")
    st.stop() # Kunci halaman sisa di bawah agar tidak tereksekusi sebelum login berhasil

# Menyimpan variabel name agar kompatibel dengan sisa kode dashboard Anda
name = st.session_state["nama_user"]

# ==========================================
# 3. HALAMAN UTAMA / DASHBOARD (SETELAH BERHASIL LOGIN)
# ==========================================

# Tombol logout rapi diletakkan di sidebar atas menggantikan fungsi pustaka lama
if st.sidebar.button("🚪 Logout dari Sistem", use_container_width=True):
    st.session_state["sudah_login"] = False
    st.session_state["nama_user"] = ""
    st.rerun()

# CUSTOMLY BACKGROUND & GAYA TAMPILAN (CSS)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FDFBF7; 
    }
    section[data-testid="stSidebar"] {
        background-color: #FFF8EE !important;
    }
    .stButton>button {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# MENAMPILKAN LOGO DI SIDEBAR
nama_file_logo = "logo.png" 

if os.path.exists(nama_file_logo):
    st.sidebar.image(nama_file_logo, use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center;'>🥚 KANDANG JAYA</h2>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.success(f"Selamat Datang, {name}!")

# MENU NAVIGASI UTAMA
menu = st.sidebar.radio(
    "Menu Navigasi",
    [
        "Dashboard",
        "Input Produksi",
        "Data Produksi",
        "Data Pendapatan",
        "Data Pengeluaran"
    ]
)

# KONSTANTA DATA
HARGA_AYAM = 1500
HARGA_BEBEK = 3000
HARGA_PUYUH = 500

BULAN_INDO = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

# FUNGSI PENDUKUNG
def format_tanggal_indo(tgl_str):
    try:
        dt = datetime.strptime(tgl_str, "%Y-%m-%d")
        return f"{dt.day} {BULAN_INDO[dt.month]} {dt.year}"
    except Exception:
        return tgl_str

def format_rupiah_kustom(val):
    try:
        return f"{int(val):,}".replace(",", ".")
    except Exception:
        return val

def ambil_jam_wib():
    waktu_utc = datetime.utcnow()
    waktu_wib = waktu_utc + timedelta(hours=7)
    return waktu_wib.strftime("%H:%M:%S")

# FUNGSI PEMBUAT PDF LAPORAN
def buat_pdf_laporan(jenis_laporan, tgl_mulai_str, tgl_selesai_str, df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=10, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    farm_style = ParagraphStyle(
        'FarmPDF', parent=styles['Heading1'], fontSize=18, leading=22,
        textColor=colors.HexColor('#8B4513'), alignment=0, spaceAfter=1
    )
    sub_style = ParagraphStyle(
        'SubJudulPDF', parent=styles['Normal'], fontSize=10, leading=13,
        textColor=colors.gray, alignment=0, spaceAfter=0
    )
    title_style = ParagraphStyle(
        'JudulPDF', parent=styles['Heading2'], fontSize=13, leading=15,
        textColor=colors.HexColor('#A0522D'), alignment=1, spaceAfter=3
    )
    date_style = ParagraphStyle(
        'TanggalPDF', parent=styles['Normal'], fontSize=10, leading=12,
        textColor=colors.HexColor('#444444'), alignment=1, spaceAfter=3
    )
    info_cetak_style = ParagraphStyle(
        'InfoCetakPDF', parent=styles['Normal'], fontSize=8.5, leading=10.5,
        textColor=colors.gray, alignment=1, spaceAfter=0
    )

    nama_file_logo_baru = "LogoLaporan.png"
    komponen_kiri = []
    
    if os.path.exists(nama_file_logo_baru):
        try:
            logo_kop = Image(nama_file_logo_baru, width=95, height=95)
            logo_kop.hAlign = 'LEFT'
            komponen_kiri.append(logo_kop)
        except Exception as e:
            print(f"Gagal memuat logo karena: {e}")
            komponen_kiri.append(Paragraph("", styles['Normal']))
    else:
        komponen_kiri.append(Spacer(65, 65))
        
    komponen_kanan = []
    komponen_kanan.append(Paragraph("<b>KURNIA SANUSI FARM</b>", farm_style))
    komponen_kanan.append(Paragraph("JL. CILENGKRANG 2 KP. MEKARSARI RT.02 RW.01 KEL. PALASARI KEC. CIBIRU KOTA BANDUNG 40615 NO.70 NO TELP : 081220861824", sub_style))
    
    lebar_kolom_kanan = letter[0] - 60 - 75 
    tabel_kop = Table([[komponen_kiri, komponen_kanan]], colWidths=[75, lebar_kolom_kanan])
    tabel_kop.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 25),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(tabel_kop)
    
    story.append(Spacer(1, 4 ))
    garis_kop = Table([[""]], colWidths=[letter[0] - 60], rowHeights=[2])
    garis_kop.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#444444')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(garis_kop)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph(jenis_laporan.upper(), title_style))
    story.append(Paragraph(f"Periode: {tgl_mulai_str} S/D {tgl_selesai_str}", date_style))
    
    waktu_cetak = (datetime.utcnow() + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M WIB")
    story.append(Paragraph(f"Dicetak pada: {waktu_cetak}", info_cetak_style))
    story.append(Spacer(1, 15))

    # =========================================================================
    # GANTI BLOK HEADERS LAMA DENGAN KODE DI BAWAH INI
    # =========================================================================
    headers = []
    # Mapping ini otomatis merapikan semua jenis kolom dari semua menu laporan Anda
    mapping_header = {
        "tanggal": "Tanggal",
        "jam": "Jam",
        "ayam": "Ayam",
        "bebek": "Bebek",
        "puyuh": "Puyuh",
        "Total": "Total",
        "keterangan": "Keterangan",
        "Jumlah (Rp)": "Jumlah (Rp)",
        "Uang Ayam (Rp)": "Uang Ayam (Rp)",
        "Uang Bebek (Rp)": "Uang Bebek (Rp)",
        "Uang Puyuh (Rp)": "Uang Puyuh (Rp)",
        "Total Pendapatan (Rp)": "Total Pendapatan (Rp)"
    }
    
    for col in df_data.columns:
        # Mengambil nama rapi dari mapping, jika tidak terdaftar gunakan nama asli kolom
        headers.append(mapping_header.get(col, col))
    # =========================================================================

    data_tabel = [headers] + df_data.values.tolist()
    for i in range(len(data_tabel)):
        for j in range(len(data_tabel[i])):
            data_tabel[i][j] = str(data_tabel[i][j])
            
    t = Table(data_tabel, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFF8EE')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#8B4513')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF8EE')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#8B4513')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# INITIALIZE DATABASE TABLES
conn.execute("""
CREATE TABLE IF NOT EXISTS produksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    jam TEXT,
    ayam INTEGER,
    bebek INTEGER,
    puyuh INTEGER
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS pengeluaran (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    jam TEXT,
    keterangan TEXT,
    jumlah REAL
)
""")
conn.commit()

# ==========================
# FITUR MENU 1: DASHBOARD
# ==========================
if menu == "Dashboard":
    # JUDUL DENGAN BACKGROUND BIRU MUDA DAN REVISI SPASI SEJAJAR
    st.markdown(
        """
        <div style="color: #31333F; font-family: sans-serif; line-height: 1.3;">
            <div style="font-size: 25px; font-weight: 700; padding: 4px 8px;background-color: #E0F2FE; display: inline-block; padding: 4px 12px; border-radius: 6px;"">
                📊 Dashboard Analisis
            </div>
            <div style="font-size: 25px; font-weight: 700; margin-left: 38px; margin-top: 2px; background-color: #E0F2FE; display: inline-block; padding: 4px 12px; border-radius: 6px;">
                Kurnia Sanusi Farm
            </div>
        </div>
        <br>
        """, 
        unsafe_allow_html=True
    )
    
    # Ambil semua data mentah untuk menentukan nilai batas min & max tanggal di komponen input
    df_raw = pd.read_sql("SELECT * FROM produksi", conn)
    df_pengeluaran_raw = pd.read_sql("SELECT * FROM pengeluaran", conn)

    if df_raw.empty:
        st.info("Belum ada data produksi untuk ditampilkan di dashboard.")
    else:
        # Menentukan rentang tanggal default (Min dan Max dari database)
        min_date_db = datetime.strptime(df_raw["tanggal"].min(), "%Y-%m-%d").date()
        max_date_db = datetime.strptime(df_raw["tanggal"].max(), "%Y-%m-%d").date()

        # --- TAMBAHAN WIDGET FILTER RENTANG TANGGAL DASHBOARD ---
        st.markdown("### 🔍 Filter Analisis Berdasarkan Periode")
        col_tgl1, col_tgl2 = st.columns(2)
        with col_tgl1:
            tgl_mulai_dash = st.date_input("Dari Tanggal", value=min_date_db, key="dash_tgl_mulai")
        with col_tgl2:
            tgl_selesai_dash = st.date_input("Sampai Tanggal", value=max_date_db, key="dash_tgl_selesai")
        
        st.divider()

        # Proses Filtering Data Produksi Berdasarkan Input Tanggal
        df_raw["tanggal_dt"] = pd.to_datetime(df_raw["tanggal"]).dt.date
        df = df_raw[(df_raw["tanggal_dt"] >= tgl_mulai_dash) & (df_raw["tanggal_dt"] <= tgl_selesai_dash)].copy()
        df = df.drop(columns=["tanggal_dt"])

        # Proses Filtering Data Pengeluaran Berdasarkan Input Tanggal
        if not df_pengeluaran_raw.empty:
            df_pengeluaran_raw["tanggal_dt"] = pd.to_datetime(df_pengeluaran_raw["tanggal"]).dt.date
            df_pengeluaran = df_pengeluaran_raw[(df_pengeluaran_raw["tanggal_dt"] >= tgl_mulai_dash) & (df_pengeluaran_raw["tanggal_dt"] <= tgl_selesai_dash)].copy()
            df_pengeluaran = df_pengeluaran.drop(columns=["tanggal_dt"])
        else:
            df_pengeluaran = df_pengeluaran_raw.copy()

        # Tampilkan info jika hasil filter kosong
        if df.empty:
            st.warning("Tidak ada data produksi pada rentang tanggal terpilih.")
        else:
            df = df.sort_values(by="tanggal").reset_index(drop=True)
            
            # Hitung kalkulasi berdasarkan data yang sudah ter-filter rentang tanggal
            total_ayam = df["ayam"].sum()
            total_bebek = df["bebek"].sum()
            total_puyuh = df["puyuh"].sum()
            
            pendapatan_ayam = total_ayam * HARGA_AYAM
            pendapatan_bebek = total_bebek * HARGA_BEBEK
            pendapatan_puyuh = total_puyuh * HARGA_PUYUH
            
            grand_total_pendapatan = pendapatan_ayam + pendapatan_bebek + pendapatan_puyuh
            grand_total_pengeluaran = df_pengeluaran["jumlah"].sum() if not df_pengeluaran.empty else 0
            keuntungan_bersih = grand_total_pendapatan - grand_total_pengeluaran
            
            # === BAGIAN METRIK KEUANGAN ===
            st.subheader("💸 Laporan Keuangan")
            c1, c2, c3 = st.columns(3)
            
            # Kolom 1 & 2 kembali menggunakan st.metric standar bawaan Streamlit
            c1.metric("💰 Total Pendapatan (Omzet)", f"Rp {format_rupiah_kustom(grand_total_pendapatan)}")
            c2.metric("💸 Total Pengeluaran", f"Rp {format_rupiah_kustom(grand_total_pengeluaran)}")
                        
            # BAGIAN KEUNTUNGAN BERSIH (KEMBALI KE BADGE HTML KUSTOM DENGAN UKURAN LEBIH BESAR)
            nominal_bersih_abs = abs(keuntungan_bersih)
            teks_rupiah = f"Rp {format_rupiah_kustom(nominal_bersih_abs)}"
                        
            if keuntungan_bersih < 0:
                warna_bg = "#fee2e2"      # Merah muda lembut
                warna_teks = "#991b1b"    # Merah tua
                simbol_panah = "↓"
                status_teks = "Rugi"
                tanda_minus = "-"
            else:
                warna_bg = "#dcfce7"      # Hijau muda lembut
                warna_teks = "#166534"    # Hijau tua
                simbol_panah = "↑"
                status_teks = "Untung"
                tanda_minus = ""
            
            # Menampilkan judul kecil di kolom 3
            c3.markdown("<p style='margin:0; font-size:14px; color:rgb(49, 51, 63); font-weight:400;'>📈 Keuntungan Bersih</p>", unsafe_allow_html=True)
                        
            # Menampilkan pill/badge dengan ukuran nominal font yang dinaikkan (font-size: 24px)
            c3.markdown(f"""
                <div style="
                    display: inline-block; 
                    background-color: {warna_bg}; 
                    color: {warna_teks}; 
                    padding: 6px 16px; 
                    border-radius: 12px; 
                    font-size: 24px; 
                    font-weight: 700;
                    margin-top: 4px;
                ">
                    {simbol_panah} {tanda_minus}{teks_rupiah} <span style="font-size: 16px; font-weight: 500;">({status_teks})</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # === BAGIAN METRIK PRODUKSI TELUR ===
            st.subheader("🥚 Laporan Produksi Telur")
            cx1, cx2, cx3 = st.columns(3)
            cx1.metric("🐔 Telur Ayam", f"{total_ayam:,}".replace(",", ".") + " Butir")
            cx2.metric("🦆 Telur Bebek", f"{total_bebek:,}".replace(",", ".") + " Butir")
            cx3.metric("🐦 Telur Puyuh", f"{total_puyuh:,}".replace(",", ".") + " Butir")

            st.divider()

            df["Total"] = df["ayam"] + df["bebek"] + df["puyuh"]

# ==========================
# FITUR MENU 2: INPUT PRODUKSI
# ==========================
# ==========================
# FITUR MENU 2: INPUT PRODUKSI (UPDATED WITH EXPENDITURE OVERWRITE)
# ==========================
elif menu == "Input Produksi":
    st.subheader("Formulir Pencatatan Harian")
    tab1, tab2 = st.tabs(["🥚 Input Produksi Telur", "💸 Input Pengeluaran Biaya"])

    # --- TAB 1: INPUT PRODUKSI TELUR ---
    with tab1:
        st.subheader("Input / Edit Produksi Harian")
        tanggal = st.date_input("Pilih Tanggal Produksi")
        str_tanggal = str(tanggal)
        str_tanggal_indo = format_tanggal_indo(str_tanggal)

        cursor = conn.cursor()
        cursor.execute("SELECT ayam, bebek, puyuh FROM produksi WHERE tanggal = ?", (str_tanggal,))
        data_ada = cursor.fetchone()

        if data_ada:
            st.warning(f"⚠️ Tanggal {str_tanggal_indo} sudah memiliki data produksi. Mengisi form ini akan meng-overwrite data tersebut.")
            default_ayam = int(data_ada[0])
            default_bebek = int(data_ada[1])
            default_puyuh = int(data_ada[2])
        else:
            default_ayam = 0
            default_bebek = 0
            default_puyuh = 0

        ayam = st.number_input("Telur Ayam (Butir)", min_value=0, value=default_ayam)
        bebek = st.number_input("Telur Bebek (Butir)", min_value=0, value=default_bebek)
        puyuh = st.number_input("Telur Puyuh (Butir)", min_value=0, value=default_puyuh)

        if data_ada:
            if st.button("🔄 Perbarui Data Produksi (Overwrite)", type="primary"):
                jam_wib = ambil_jam_wib()
                conn.execute("UPDATE produksi SET ayam = ?, bebek = ?, puyuh = ?, jam = ? WHERE tanggal = ?", (ayam, bebek, puyuh, jam_wib, str_tanggal))
                conn.commit()
                st.success(f"Data tanggal {str_tanggal_indo} berhasil diperbarui pada jam {jam_wib} WIB!")
                st.rerun()
        else:
            if st.button("📥 Simpan Data Produksi Baru"):
                jam_wib = ambil_jam_wib()
                conn.execute("INSERT INTO produksi (tanggal, jam, ayam, bebek, puyuh) VALUES (?, ?, ?, ?, ?)", (str_tanggal, jam_wib, ayam, bebek, puyuh))
                conn.commit()
                st.success(f"Data baru berhasil disimpan pada jam {jam_wib} WIB.")
                st.rerun()

    # --- TAB 2: INPUT PENGELUARAN BIAYA (DENGAN FITUR EDIT/OVERWRITE) ---
    with tab2:
        st.subheader("Input / Edit Pengeluaran Operasional / Pakan")
        tgl_pengeluaran = st.date_input("Tanggal Pengeluaran")
        str_tgl_keluar = str(tgl_pengeluaran)
        str_tgl_keluar_indo = format_tanggal_indo(str_tgl_keluar)

        # Cek apakah tanggal pengeluaran ini sudah pernah diinput sebelumnya
        cursor_keluar = conn.cursor()
        cursor_keluar.execute("SELECT keterangan, jumlah FROM pengeluaran WHERE tanggal = ?", (str_tgl_keluar,))
        data_keluar_ada = cursor_keluar.fetchone()

        if data_keluar_ada:
            st.warning(f"⚠️ Tanggal {str_tgl_keluar_indo} sudah memiliki catatan pengeluaran. Mengisi form ini akan meng-overwrite data tersebut.")
            default_keterangan = str(data_keluar_ada[0])
            default_biaya = float(data_keluar_ada[1])
        else:
            default_keterangan = ""
            default_biaya = 0.0

        keterangan = st.text_input("Keterangan Pengeluaran (Contoh: Beli pakan ayam, obat bebek)", value=default_keterangan)
        jumlah_biaya = st.number_input("Jumlah Biaya (Rp)", min_value=0.0, step=500.0, value=default_biaya)
        
        if data_keluar_ada:
            if st.button("🔄 Perbarui Nota Pengeluaran (Overwrite)", type="primary", key="btn_overwrite_keluar"):
                if keterangan == "":
                    st.error("Keterangan tidak boleh kosong!")
                elif jumlah_biaya <= 0:
                    st.error("Jumlah biaya harus lebih besar dari 0!")
                else:
                    jam_wib_biaya = ambil_jam_wib()
                    conn.execute("UPDATE pengeluaran SET keterangan = ?, jumlah = ?, jam = ? WHERE tanggal = ?", (keterangan, jumlah_biaya, jam_wib_biaya, str_tgl_keluar))
                    conn.commit()
                    st.success(f"Nota pengeluaran tanggal {str_tgl_keluar_indo} berhasil diperbarui pada jam {jam_wib_biaya} WIB!")
                    st.rerun()
        else:
            if st.button("📥 Simpan Nota Pengeluaran Baru", type="secondary", key="btn_simpan_keluar"):
                if keterangan == "":
                    st.error("Keterangan tidak boleh kosong!")
                elif jumlah_biaya <= 0:
                    st.error("Jumlah biaya harus lebih besar dari 0!")
                else:
                    jam_wib_biaya = ambil_jam_wib()
                    conn.execute("INSERT INTO pengeluaran (tanggal, jam, keterangan, jumlah) VALUES (?, ?, ?, ?)", (str_tgl_keluar, jam_wib_biaya, keterangan, jumlah_biaya))
                    conn.commit()
                    st.success(f"Pengeluaran baru berhasil dicatat pada jam {jam_wib_biaya} WIB!")
                    st.rerun()

# ==========================
# FITUR MENU 3: DATA PRODUKSI
# ==========================
elif menu == "Data Produksi":
    st.subheader("📦 Data Rekap Produksi Telur Harian")
    df_all = pd.read_sql("SELECT id, tanggal, jam, ayam, bebek, puyuh FROM produksi ORDER BY tanggal DESC", conn)

    if df_all.empty:
        st.info("Belum ada data produksi.")
    else:
        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal", value=datetime.strptime(df_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal", value=datetime.strptime(df_all["tanggal"].max(), "%Y-%m-%d").date())

        df_all["tanggal_dt"] = pd.to_datetime(df_all["tanggal"]).dt.date
        df_filtered = df_all[(df_all["tanggal_dt"] >= tgl_mulai) & (df_all["tanggal_dt"] <= tgl_selesai)].copy()
        df_filtered = df_filtered.drop(columns=["tanggal_dt"])

        if df_filtered.empty:
            st.info("Tidak ada data produksi pada rentang tanggal tersebut.")
        else:
            df_filtered["Total"] = df_filtered["ayam"] + df_filtered["bebek"] + df_filtered["puyuh"]
            df_tabel = df_filtered.drop(columns=["id"], errors="ignore").sort_values(by="tanggal", ascending=False)
            
            total_ayam_s = df_tabel["ayam"].sum()
            total_bebek_s = df_tabel["bebek"].sum()
            total_puyuh_s = df_tabel["puyuh"].sum()
            total_semua_s = df_tabel["Total"].sum()
            
            df_tabel["tanggal"] = df_tabel["tanggal"].apply(format_tanggal_indo)
            
            row_total = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-", 
                "ayam": total_ayam_s, "bebek": total_bebek_s, 
                "puyuh": total_puyuh_s, "Total": total_semua_s
            }])
            df_tabel = pd.concat([df_tabel, row_total], ignore_index=True)

            df_tampil_produksi = df_tabel.rename(columns={"tanggal": "Tanggal", "jam": "Jam", "ayam": "Ayam", "bebek": "Bebek", "puyuh": "Puyuh"})
            st.dataframe(df_tampil_produksi, use_container_width=True, hide_index=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                pdf_data = buat_pdf_laporan("Laporan Rekap Produksi Telur", format_tanggal_indo(str(tgl_mulai)), format_tanggal_indo(str(tgl_selesai)), df_tabel)
                st.download_button(
                    label="📄 Unduh / Cetak Laporan PDF",
                    data=pdf_data,
                    file_name=f"Laporan_Produksi_{tgl_mulai}_to_{tgl_selesai}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            with btn_col2:
                excel = "rekap_telur_filter.xlsx"
                df_tampil_produksi.to_excel(excel, index=False)
                with open(excel, "rb") as file:
                    st.download_button("⬇ Download File Excel", file, file_name=f"rekap_produksi_{tgl_mulai}_to_{tgl_selesai}.xlsx", use_container_width=True)

        st.divider()
        st.subheader("🗑️ Hapus Data Produksi")
        pilihan_data = {row["id"]: f"{format_tanggal_indo(row['tanggal'])} (Jam {row['jam']}) [🐔: {row['ayam']} | 🦆: {row['bebek']}]" for _, row in df_all.iterrows()}
        id_terpilih = st.selectbox("Pilih baris data produksi yang ingin dihapus permanen:", options=list(pilihan_data.keys()), format_func=lambda x: pilihan_data[x])
        
        if st.button("Hapus Permanen", type="primary"):
            conn.execute("DELETE FROM produksi WHERE id = ?", (id_terpilih,))
            conn.commit()
            st.success("Data produksi berhasil dihapus!")
            st.rerun()

# ==========================
# FITUR MENU 4: DATA PENDAPATAN
# ==========================
elif menu == "Data Pendapatan":
    st.subheader("💰 Laporan Pendapatan Keuangan (Omzet)")
    df_dana_all = pd.read_sql("SELECT tanggal, jam, ayam, bebek, puyuh FROM produksi", conn)

    if df_dana_all.empty:
        st.info("Belum ada data transaksi keuangan.")
    else:
        df_dana_all = df_dana_all.sort_values(by="tanggal").reset_index(drop=True)

        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal ", value=datetime.strptime(df_dana_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal ", value=datetime.strptime(df_dana_all["tanggal"].max(), "%Y-%m-%d").date())

        df_dana_all["tanggal_dt"] = pd.to_datetime(df_dana_all["tanggal"]).dt.date
        df_dana = df_dana_all[(df_dana_all["tanggal_dt"] >= tgl_mulai) & (df_dana_all["tanggal_dt"] <= tgl_selesai)].copy()
        df_dana = df_dana.drop(columns=["tanggal_dt"])

        if df_dana.empty:
            st.info("Tidak ada data pendapatan pada rentang tanggal tersebut.")
        else:
            df_dana["Uang Ayam (Rp)"] = df_dana["ayam"] * HARGA_AYAM
            df_dana["Uang Bebek (Rp)"] = df_dana["bebek"] * HARGA_BEBEK
            df_dana["Uang Puyuh (Rp)"] = df_dana["puyuh"] * HARGA_PUYUH
            df_dana["Total Pendapatan (Rp)"] = (df_dana["Uang Ayam (Rp)"] + df_dana["Uang Bebek (Rp)"] + df_dana["Uang Puyuh (Rp)"])

            df_tabel_uang = df_dana.drop(columns=["ayam", "bebek", "puyuh"]).sort_values(by="tanggal", ascending=False)
            
            t_u_ayam = df_tabel_uang["Uang Ayam (Rp)"].sum()
            t_u_bebek = df_tabel_uang["Uang Bebek (Rp)"].sum()
            t_u_puyuh = df_tabel_uang["Uang Puyuh (Rp)"].sum()
            t_u_grand = df_tabel_uang["Total Pendapatan (Rp)"].sum()
            
            df_tabel_uang["tanggal"] = df_tabel_uang["tanggal"].apply(format_tanggal_indo)
            
            row_total_uang = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-",
                "Uang Ayam (Rp)": t_u_ayam, "Uang Bebek (Rp)": t_u_bebek,
                "Uang Puyuh (Rp)": t_u_puyuh, "Total Pendapatan (Rp)": t_u_grand
            }])
            df_tabel_uang = pd.concat([df_tabel_uang, row_total_uang], ignore_index=True)

            df_tabel_uang["Uang Ayam (Rp)"] = df_tabel_uang["Uang Ayam (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Uang Bebek (Rp)"] = df_tabel_uang["Uang Bebek (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Uang Puyuh (Rp)"] = df_tabel_uang["Uang Puyuh (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Total Pendapatan (Rp)"] = df_tabel_uang["Total Pendapatan (Rp)"].apply(format_rupiah_kustom)

            df_tampil_pendapatan = df_tabel_uang.rename(columns={"tanggal": "Tanggal", "jam": "Jam"})
            st.dataframe(df_tampil_pendapatan, use_container_width=True, hide_index=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                pdf_pendapatan = buat_pdf_laporan("Laporan Pendapatan Keuangan", format_tanggal_indo(str(tgl_mulai)), format_tanggal_indo(str(tgl_selesai)), df_tabel_uang)
                st.download_button(
                    label="📄 Unduh / Cetak Laporan PDF",
                    data=pdf_pendapatan,
                    file_name=f"Laporan_Pendapatan_{tgl_mulai}_to_{tgl_selesai}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            with btn_col2:
                excel_keuangan = "rekap_pendapatan_filter.xlsx"
                df_tampil_pendapatan.to_excel(excel_keuangan, index=False)
                with open(excel_keuangan, "rb") as file_keuangan:
                    st.download_button("⬇ Download File Excel", file_keuangan, file_name=f"rekap_pendapatan_{tgl_mulai}_to_{tgl_selesai}.xlsx", use_container_width=True)

            st.divider()
            st.subheader("📊 Grafik Distribusi Keuangan Harian")
            fig_dana = px.line(
                df_dana, x="tanggal", y=["Uang Ayam (Rp)", "Uang Bebek (Rp)", "Uang Puyuh (Rp)", "Total Pendapatan (Rp)"],
                markers=True, title="Tren Pendapatan Omzet Rupiah",
                color_discrete_map={"Uang Ayam (Rp)": "#8B4513", "Uang Bebek (Rp)": "#87CEFA", "Uang Puyuh (Rp)": "#D3D3D3", "Total Pendapatan (Rp)": "#00FF00"}
            )
            fig_dana.update_xaxes(tickformat="%d %b %Y")
            fig_dana.update_layout(template="plotly_white")
            st.plotly_chart(fig_dana, use_container_width=True)

# ==========================
# FITUR MENU 5: DATA PENGELUARAN
# ==========================
elif menu == "Data Pengeluaran":
    st.subheader("💸 Laporan Pengeluaran Operasional / Pembelian Pakan")
    df_keluar_all = pd.read_sql("SELECT id, tanggal, jam, keterangan, jumlah AS 'Jumlah (Rp)' FROM pengeluaran ORDER BY tanggal DESC", conn)

    if df_keluar_all.empty:
        st.info("Belum ada catatan pengeluaran biaya.")
    else:
        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal  ", value=datetime.strptime(df_keluar_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal  ", value=datetime.strptime(df_keluar_all["tanggal"].max(), "%Y-%m-%d").date())

        df_keluar_all["tanggal_dt"] = pd.to_datetime(df_keluar_all["tanggal"]).dt.date
        df_keluar_filtered = df_keluar_all[(df_keluar_all["tanggal_dt"] >= tgl_mulai) & (df_keluar_all["tanggal_dt"] <= tgl_selesai)].copy()
        df_keluar_filtered = df_keluar_filtered.drop(columns=["tanggal_dt"])

        if df_keluar_filtered.empty:
            st.info("Tidak ada data pengeluaran pada rentang tanggal tersebut.")
        else:
            df_tabel_keluar = df_keluar_filtered.drop(columns=["id"], errors="ignore")
            
            total_pengeluaran_s = df_tabel_keluar["Jumlah (Rp)"].sum()
            
            df_tabel_keluar["tanggal"] = df_tabel_keluar["tanggal"].apply(format_tanggal_indo)
            
            row_total_keluar = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-", "keterangan": "Total Biaya Operasional", "Jumlah (Rp)": total_pengeluaran_s
            }])
            df_tabel_keluar = pd.concat([df_tabel_keluar, row_total_keluar], ignore_index=True)

            df_tabel_keluar["Jumlah (Rp)"] = df_tabel_keluar["Jumlah (Rp)"].apply(format_rupiah_kustom)

            df_tampil_pengeluaran = df_tabel_keluar.rename(columns={"tanggal": "Tanggal", "jam": "Jam", "keterangan": "Keterangan"})
            st.dataframe(df_tampil_pengeluaran, use_container_width=True, hide_index=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                pdf_pengeluaran = buat_pdf_laporan("Laporan Pengeluaran Operasional", format_tanggal_indo(str(tgl_mulai)), format_tanggal_indo(str(tgl_selesai)), df_tabel_keluar)
                st.download_button(
                    label="📄 Unduh / Cetak Laporan PDF",
                    data=pdf_pengeluaran,
                    file_name=f"Laporan_Pengeluaran_{tgl_mulai}_to_{tgl_selesai}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            with btn_col2:
                excel_keluar = "rekap_pengeluaran_filter.xlsx"
                df_tampil_pengeluaran.to_excel(excel_keluar, index=False)
                with open(excel_keluar, "rb") as file_keluar:
                    st.download_button("⬇ Download File Excel", file_keluar, file_name=f"rekap_pengeluaran_{tgl_mulai}_to_{tgl_selesai}.xlsx", use_container_width=True)

        st.divider()
        st.subheader("🗑️ Hapus Nota Pengeluaran")
        pilihan_keluar = {row["id"]: f"{format_tanggal_indo(row['tanggal'])} (Jam {row['jam']}) — {row['keterangan']} [Rp {row['Jumlah (Rp)']:,}]" for _, row in df_keluar_all.iterrows()}
        id_keluar_terpilih = st.selectbox("Pilih nota pengeluaran yang ingin dihapus:", options=list(pilihan_keluar.keys()), format_func=lambda x: pilihan_keluar[x])

        if st.button("Hapus Nota", type="primary"):
            conn.execute("DELETE FROM pengeluaran WHERE id = ?", (id_keluar_terpilih,))
            conn.commit()
            st.success("Nota pengeluaran berhasil dihapus!")
            st.rerun()
