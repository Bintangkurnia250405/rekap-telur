import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import conn
from datetime import datetime, timedelta
import os
import io

# Import untuk membuat PDF resmi
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(
    page_title="Rekap Produksi Telur",
    page_icon="🥚",
    layout="wide"
)

# ==========================================
# CUSTOMLY BACKGROUND & GAYA TAMPILAN (CSS)
# ==========================================
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

# ==========================================
# MENAMPILKAN LOGO DI SIDEBAR
# ==========================================
nama_file_logo = "logo.png" 

if os.path.exists(nama_file_logo):
    st.sidebar.image(nama_file_logo, use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center;'>🥚 KANDANG JAYA</h2>", unsafe_allow_html=True)

st.sidebar.divider()

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

HARGA_AYAM = 1500
HARGA_BEBEK = 3000
HARGA_PUYUH = 500

# Kamus bulan untuk format teks Indonesia
BULAN_INDO = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def format_tanggal_indo(tgl_str):
    """Mengubah format YYYY-MM-DD menjadi DD Bulan YYYY (Contoh: 27 Juni 2026)"""
    try:
        dt = datetime.strptime(tgl_str, "%Y-%m-%d")
        return f"{dt.day} {BULAN_INDO[dt.month]} {dt.year}"
    except Exception:
        return tgl_str

def format_rupiah_kustom(val):
    """Mengubah angka nominal menjadi format string dengan titik (Contoh: 45000 -> 45.000)"""
    try:
        return f"{int(val):,}".replace(",", ".")
    except Exception:
        return val

def ambil_jam_wib():
    waktu_utc = datetime.utcnow()
    waktu_wib = waktu_utc + timedelta(hours=7)
    return waktu_wib.strftime("%H:%M:%S")

# Fungsi Pembuat PDF Laporan dengan Format Kop Surat Resmi Bergaris
def buat_pdf_laporan(jenis_laporan, tgl_mulai_str, tgl_selesai_str, df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Gaya Nama Farm (Besar & Cokelat)
    farm_style = ParagraphStyle(
        'FarmPDF',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#8B4513'),
        alignment=0,
        spaceAfter=1
    )
    
    # Gaya Alamat & Cetak (Kecil, Abu-abu, Rata Kiri)
    sub_style = ParagraphStyle(
        'SubJudulPDF',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.gray,
        alignment=0,
        spaceAfter=0
    )
    
    # Gaya Judul Laporan di Bawah Garis (Sedikit Lebih Besar & Rata Kiri)
    title_style = ParagraphStyle(
        'JudulPDF',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#A0522D'),
        alignment=0,
        spaceAfter=2
    )
    
    # Gaya Periode Tanggal di Bawah Garis
    date_style = ParagraphStyle(
        'TanggalPDF',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#444444'),
        alignment=0,
        spaceAfter=2
    )

    # --- MEMBUAT KOP UTAMA (DI ATAS GARIS) ---
    nama_file_logo_baru = "LogoLaporan.png"
    komponen_kiri = []
    
    if os.path.exists(nama_file_logo_baru):
        try:
            logo_kop = Image(nama_file_logo_baru, width=60, height=60)
            logo_kop.hAlign = 'LEFT'
            komponen_kiri.append(logo_kop)
        except Exception:
            komponen_kiri.append(Paragraph("", styles['Normal']))
    else:
        komponen_kiri.append(Spacer(60, 60))
    
    komponen_kanan = []
    komponen_kanan.append(Paragraph("<b>KURNIA SANUSI FARM</b>", farm_style))
    komponen_kanan.append(Paragraph("JL. CILENGKRANG 2 KP. MEKARSARI RT.02 RW.01 KEL. PALASARI KEC. CIBIRU KOTA BANDUNG 40615 NO.70", sub_style))
    
    lebar_kolom_kanan = letter[0] - 60 - 75 
    tabel_kop = Table([[komponen_kiri, komponen_kanan]], colWidths=[75, lebar_kolom_kanan])
    tabel_kop.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(tabel_kop)
    
    # GARIS PEMBATAS SOLID
    story.append(Spacer(1, 8))
    garis_kop = Table([[""]], colWidths=[letter[0] - 60], rowHeights=[2])
    garis_kop.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#444444')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(garis_kop)
    
    # --- DETAIL INFORMASI (DI BAWAH GARIS) ---
    story.append(Spacer(1, 10))
    story.append(Paragraph(jenis_laporan.upper(), title_style))
    story.append(Paragraph(f"Periode: {tgl_mulai_str} S/D {tgl_selesai_str}", date_style))
    
    waktu_cetak = (datetime.utcnow() + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M WIB")
    story.append(Paragraph(f"Dicetak pada: {waktu_cetak}", sub_style))
    story.append(Spacer(1, 15))

    # --- DATA TABEL LAPORAN ---
    headers = []
    for col in df_data.columns:
        if col == "tanggal":
            headers.append("Tanggal")
        elif col == "jam":
            headers.append("Jam")
        else:
            headers.append(col)

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
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

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

try:
    conn.execute("SELECT jam FROM produksi LIMIT 1")
except sqlite3.OperationalError:
    conn.execute("ALTER TABLE produksi ADD COLUMN jam TEXT DEFAULT '-'")
    conn.commit()

# ==========================
# 1. DASHBOARD
# ==========================
if menu == "Dashboard":
    st.title("🥚 Rekap Produksi & Keuangan")
    df = pd.read_sql("SELECT * FROM produksi", conn)
    df_pengeluaran = pd.read_sql("SELECT * FROM pengeluaran", conn)

    if df.empty:
        st.info("Belum ada data produksi.")
    else:
        df = df.sort_values(by="tanggal").reset_index(drop=True)
        
        total_ayam = df["ayam"].sum()
        total_bebek = df["bebek"].sum()
        total_puyuh = df["puyuh"].sum()
        
        pendapatan_ayam = total_ayam * HARGA_AYAM
        pendapatan_bebek = total_bebek * HARGA_BEBEK
        pendapatan_puyuh = total_puyuh * HARGA_PUYUH
        
        grand_total_pendapatan = pendapatan_ayam + pendapatan_bebek + pendapatan_puyuh
        grand_total_pengeluaran = df_pengeluaran["jumlah"].sum() if not df_pengeluaran.empty else 0
        keuntungan_bersih = grand_total_pendapatan - grand_total_pengeluaran
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Pendapatan (Omzet)", f"Rp {grand_total_pendapatan:,}".replace(",", "."))
        c2.metric("💸 Total Pengeluaran", f"Rp {grand_total_pengeluaran:,}".replace(",", "."))
        c3.metric("📈 Keuntungan Bersih", f"Rp {keuntungan_bersih:,}".replace(",", "."))

        st.divider()
        
        st.subheader("📦 Total Produksi Telur")
        cx1, cx2, cx3 = st.columns(3)
        cx1.metric("🐔 Telur Ayam", f"{total_ayam:,}".replace(",", ".") + " butir")
        cx2.metric("🦆 Telur Bebek", f"{total_bebek:,}".replace(",", ".") + " butir")
        cx3.metric("🐦 Telur Puyuh", f"{total_puyuh:,}".replace(",", ".") + " butir")

        st.divider()

        df["Total"] = df["ayam"] + df["bebek"] + df["puyuh"]

        fig = px.line(
            df, x="tanggal", y=["ayam", "bebek", "puyuh"], markers=True,
            title="Grafik Tren Produksi Harian",
            color_discrete_map={"ayam": "#8B4513", "bebek": "#87CEFA", "puyuh": "#ffff00"}
        )
        fig.update_xaxes(tickformat="%d %b %Y")
        fig.update_layout(legend_title="Jenis Telur", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# ==========================
# 2. INPUT PRODUKSI & PENGELUARAN
# ==========================
elif menu == "Input Produksi":
    st.subheader("Formulir Pencatatan Harian")
    tab1, tab2 = st.tabs(["🥚 Input Produksi Telur", "💸 Input Pengeluaran Biaya"])

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

    with tab2:
        st.subheader("Input Pengeluaran Operasional / Pakan")
        tgl_pengeluaran = st.date_input("Tanggal Pengeluaran")
        keterangan = st.text_input("Keterangan Pengeluaran (Contoh: Beli pakan ayam, obat bebek)")
        jumlah_biaya = st.number_input("Jumlah Biaya (Rp)", min_value=0.0, step=500.0)
        
        if st.button("📥 Simpan Nota Pengeluaran", type="secondary"):
            if keterangan == "":
                st.error("Keterangan tidak boleh kosong!")
            elif jumlah_biaya <= 0:
                st.error("Jumlah biaya harus lebih besar dari 0!")
            else:
                jam_wib_biaya = ambil_jam_wib()
                conn.execute("INSERT INTO pengeluaran (tanggal, jam, keterangan, jumlah) VALUES (?, ?, ?, ?)", (str(tgl_pengeluaran), jam_wib_biaya, keterangan, jumlah_biaya))
                conn.commit()
                st.success(f"Pengeluaran berhasil dicatat pada jam {jam_wib_biaya} WIB!")
                st.rerun()

# ==========================
# 3. DATA PRODUKSI
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
            
            # 1. Hitung total per kolom numerik sebelum format diubah
            total_ayam_s = df_tabel["ayam"].sum()
            total_bebek_s = df_tabel["bebek"].sum()
            total_puyuh_s = df_tabel["puyuh"].sum()
            total_semua_s = df_tabel["Total"].sum()
            
            # 2. Ubah format kolom tanggal ke Indonesia
            df_tabel["tanggal"] = df_tabel["tanggal"].apply(format_tanggal_indo)
            
            # 3. Buat baris Total baru dan gabungkan ke tabel paling bawah
            row_total = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-", 
                "ayam": total_ayam_s, "bebek": total_bebek_s, 
                "puyuh": total_puyuh_s, "Total": total_semua_s
            }])
            df_tabel = pd.concat([df_tabel, row_total], ignore_index=True)

            # Mengubah nama kolom agar berhuruf kapital di awal ("Tanggal" & "Jam") saat ditampilkan di Streamlit
            df_tampil_produksi = df_tabel.rename(columns={"tanggal": "Tanggal", "jam": "Jam", "ayam": "Ayam", "bebek": "Bebek", "puyuh": "Puyuh"})
            st.dataframe(df_tampil_produksi, use_container_width=True, hide_index=True)

            # Tombol Cetak / Simpan Berformat File Resmi
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
# 4. DATA PENDAPATAN
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
            
            # 1. Hitung total uang per jenis telur
            t_u_ayam = df_tabel_uang["Uang Ayam (Rp)"].sum()
            t_u_bebek = df_tabel_uang["Uang Bebek (Rp)"].sum()
            t_u_puyuh = df_tabel_uang["Uang Puyuh (Rp)"].sum()
            t_u_grand = df_tabel_uang["Total Pendapatan (Rp)"].sum()
            
            # 2. Ubah format kolom tanggal ke format Indonesia
            df_tabel_uang["tanggal"] = df_tabel_uang["tanggal"].apply(format_tanggal_indo)
            
            # 3. Buat baris Total baru dan tempel di paling bawah
            row_total_uang = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-",
                "Uang Ayam (Rp)": t_u_ayam, "Uang Bebek (Rp)": t_u_bebek,
                "Uang Puyuh (Rp)": t_u_puyuh, "Total Pendapatan (Rp)": t_u_grand
            }])
            df_tabel_uang = pd.concat([df_tabel_uang, row_total_uang], ignore_index=True)

            # PERBAIKAN FORMAT UANG: Mengubah tampilan angka menggunakan format titik (.)
            df_tabel_uang["Uang Ayam (Rp)"] = df_tabel_uang["Uang Ayam (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Uang Bebek (Rp)"] = df_tabel_uang["Uang Bebek (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Uang Puyuh (Rp)"] = df_tabel_uang["Uang Puyuh (Rp)"].apply(format_rupiah_kustom)
            df_tabel_uang["Total Pendapatan (Rp)"] = df_tabel_uang["Total Pendapatan (Rp)"].apply(format_rupiah_kustom)

            # Mengubah nama kolom agar berhuruf kapital di awal ("Tanggal" & "Jam") saat ditampilkan di Streamlit
            df_tampil_pendapatan = df_tabel_uang.rename(columns={"tanggal": "Tanggal", "jam": "Jam"})
            st.dataframe(df_tampil_pendapatan, use_container_width=True, hide_index=True)

            # Tombol Cetak / Simpan Berformat File Resmi
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
# 5. DATA PENGELUARAN
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
            
            # 1. Hitung total pengeluaran rupiah sebelum format diubah
            total_pengeluaran_s = df_tabel_keluar["Jumlah (Rp)"].sum()
            
            # 2. Ubah format kolom tanggal ke format Indonesia
            df_tabel_keluar["tanggal"] = df_tabel_keluar["tanggal"].apply(format_tanggal_indo)
            
            # 3. Buat baris Total baru dan tempel di paling bawah
            row_total_keluar = pd.DataFrame([{
                "tanggal": "TOTAL", "jam": "-", "keterangan": "Total Biaya Operasional", "Jumlah (Rp)": total_pengeluaran_s
            }])
            df_tabel_keluar = pd.concat([df_tabel_keluar, row_total_keluar], ignore_index=True)

            # PERBAIKAN FORMAT UANG: Mengubah tampilan nominal jumlah pengeluaran menggunakan titik (.)
            df_tabel_keluar["Jumlah (Rp)"] = df_tabel_keluar["Jumlah (Rp)"].apply(format_rupiah_kustom)

            # Mengubah nama kolom agar berhuruf kapital di awal ("Tanggal" & "Jam") saat ditampilkan di Streamlit
            df_tampil_pengeluaran = df_tabel_keluar.rename(columns={"tanggal": "Tanggal", "jam": "Jam", "keterangan": "Keterangan"})
            st.dataframe(df_tampil_pengeluaran, use_container_width=True, hide_index=True)

            # Tombol Cetak / Simpan Berformat File Resmi
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
