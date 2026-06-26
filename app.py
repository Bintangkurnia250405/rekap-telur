import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import conn
from datetime import datetime, timedelta  # <-- Ditambahkan timedelta untuk konversi WIB

st.set_page_config(
    page_title="Rekap Produksi Telur",
    page_icon="🥚",
    layout="wide"
)

st.title("🥚 Rekap Produksi, Pendapatan & Pengeluaran Telur")

# Pilihan menu
menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Input Produksi",
        "Data Produksi",
        "Data Pendapatan",
        "Data Pengeluaran"
    ]
)

# Konstanta Harga Satuan Telur
HARGA_AYAM = 1500
HARGA_BEBEK = 3000
HARGA_PUYUH = 500

# Fungsi pembantu untuk mengambil jam WIB saat ini (UTC +7)
def ambil_jam_wib():
    waktu_utc = datetime.utcnow()
    waktu_wib = waktu_utc + timedelta(hours=7)
    return waktu_wib.strftime("%H:%M:%S")

# Buat tabel pengeluaran otomatis jika belum ada di database
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

# Cek apakah kolom jam sudah ada di tabel produksi (untuk database lama)
try:
    conn.execute("SELECT jam FROM produksi LIMIT 1")
except sqlite3.OperationalError:
    conn.execute("ALTER TABLE produksi ADD COLUMN jam TEXT DEFAULT '-'")
    conn.commit()

# ==========================
# DASHBOARD
# ==========================

if menu == "Dashboard":

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
        
        # Tampilan Ringkasan Keuangan Utama
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Pendapatan (Omzet)", f"Rp {grand_total_pendapatan:,}")
        c2.metric("💸 Total Pengeluaran", f"Rp {grand_total_pengeluaran:,}")
        c3.metric("📈 Keuntungan Bersih", f"Rp {keuntungan_bersih:,}")

        st.divider()
        
        # Ringkasan Stok Butir Telur
        st.subheader("📦 Total Produksi Telur")
        cx1, cx2, cx3 = st.columns(3)
        cx1.metric("🐔 Telur Ayam", f"{total_ayam:,} butir")
        cx2.metric("🦆 Telur Bebek", f"{total_bebek:,} butir")
        cx3.metric("🐦 Telur Puyuh", f"{total_puyuh:,} butir")

        st.divider()

        df["Total"] = df["ayam"] + df["bebek"] + df["puyuh"]

        fig = px.line(
            df,
            x="tanggal",
            y=["ayam", "bebek", "puyuh"],
            markers=True,
            title="Grafik Tren Produksi Harian",
            color_discrete_map={
                "ayam": "#8B4513",
                "bebek": "#87CEFA",
                "puyuh": "#D3D3D3"
            }
        )
        fig.update_layout(legend_title="Jenis Telur", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# ==========================
# INPUT PRODUKSI & PENGELUARAN
# ==========================

elif menu == "Input Produksi":

    tab1, tab2 = st.tabs(["🥚 Input Produksi Telur", "💸 Input Pengeluaran Biaya"])

    with tab1:
        st.subheader("Input / Edit Produksi Harian")

        tanggal = st.date_input("Pilih Tanggal Produksi")
        str_tanggal = str(tanggal)

        cursor = conn.cursor()
        cursor.execute("SELECT ayam, bebek, puyuh FROM produksi WHERE tanggal = ?", (str_tanggal,))
        data_ada = cursor.fetchone()

        if data_ada:
            st.warning(f"⚠️ Tanggal {str_tanggal} sudah memiliki data produksi. Mengisi form ini akan meng-overwrite data tersebut.")
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
                jam_wib = ambil_jam_wib()  # Dapatkan waktu Indonesia saat tombol diklik
                conn.execute(
                    """
                    UPDATE produksi 
                    SET ayam = ?, bebek = ?, puyuh = ?, jam = ?
                    WHERE tanggal = ?
                    """,
                    (ayam, bebek, puyuh, jam_wib, str_tanggal)
                )
                conn.commit()
                st.success(f"Data tanggal {str_tanggal} berhasil diperbarui pada jam {jam_wib} WIB!")
                st.rerun()
        else:
            if st.button("📥 Simpan Data Produksi Baru"):
                jam_wib = ambil_jam_wib()  # Dapatkan waktu Indonesia saat tombol diklik
                conn.execute(
                    """
                    INSERT INTO produksi (tanggal, jam, ayam, bebek, puyuh) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (str_tanggal, jam_wib, ayam, bebek, puyuh)
                )
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
                jam_wib_biaya = ambil_jam_wib()  # Dapatkan waktu Indonesia saat tombol diklik
                conn.execute(
                    """
                    INSERT INTO pengeluaran (tanggal, jam, keterangan, jumlah)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(tgl_pengeluaran), jam_wib_biaya, keterangan, jumlah_biaya)
                )
                conn.commit()
                st.success(f"Pengeluaran berhasil dicatat pada jam {jam_wib_biaya} WIB!")
                st.rerun()

# ==========================
# DATA PRODUKSI
# ==========================

elif menu == "Data Produksi":

    df = pd.read_sql(
        "SELECT id, tanggal, jam, ayam, bebek, puyuh FROM produksi ORDER BY tanggal DESC",
        conn
    )

    if df.empty:
        st.warning("Belum ada data.")
    else:
        df["Total"] = df["ayam"] + df["bebek"] + df["puyuh"]

        st.dataframe(
            df.drop(columns=["id"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        excel = "rekap_telur.xlsx"
        df.drop(columns=["id"], errors="ignore").to_excel(excel, index=False)

        with open(excel, "rb") as file:
            st.download_button("⬇ Download Excel Produksi", file, file_name=excel)
        
        st.divider()
        st.subheader("🗑️ Hapus Data Produksi")
        
        pilihan_data = {
            row["id"]: f"{row['tanggal']} (Jam {row['jam']}) [🐔: {row['ayam']} | 🦆: {row['bebek']}]"
            for _, row in df.iterrows()
        }
        
        id_terpilih = st.selectbox(
            "Pilih baris data produksi yang ingin dihapus permanen:",
            options=list(pilihan_data.keys()),
            format_func=lambda x: pilihan_data[x]
        )
        
        if st.button("Hapus Permanen", type="primary"):
            conn.execute("DELETE FROM produksi WHERE id = ?", (id_terpilih,))
