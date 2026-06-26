import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import conn
from datetime import datetime, timedelta

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
    # Jika baris di atas error saat dijalankan, ganti ke standar:
    # conn.execute("ALTER TABLE produksi ADD COLUMN jam TEXT DEFAULT '-'")
    conn.commit()

# ==========================
# 1. DASHBOARD
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
# 2. INPUT PRODUKSI & PENGELUARAN
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
                jam_wib = ambil_jam_wib()
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
                jam_wib = ambil_jam_wib()
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
                jam_wib_biaya = ambil_jam_wib()
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
# 3. DATA PRODUKSI (DENGAN FILTER TANGGAL)
# ==========================

elif menu == "Data Produksi":
    st.subheader("📦 Data Rekap Produksi Telur Harian")

    # Ambil semua data terlebih dahulu untuk menentukan range tanggal default
    df_all = pd.read_sql("SELECT id, tanggal, jam, ayam, bebek, puyuh FROM produksi ORDER BY tanggal DESC", conn)

    if df_all.empty:
        st.warning("Belum ada data produksi.")
    else:
        # Tambahkan Filter Rentang Tanggal di bagian atas halaman
        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal", value=datetime.strptime(df_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal", value=datetime.strptime(df_all["tanggal"].max(), "%Y-%m-%d").date())

        # Filter dataframe berdasarkan tanggal yang dipilih
        df_all["tanggal_dt"] = pd.to_datetime(df_all["tanggal"]).dt.date
        df = df_all[(df_all["tanggal_dt"] >= tgl_mulai) & (df_all["tanggal_dt"] <= tgl_selesai)].copy()
        df = df.drop(columns=["tanggal_dt"])

        if df.empty:
            st.info("Tidak ada data produksi pada rentang tanggal tersebut.")
        else:
            df["Total"] = df["ayam"] + df["bebek"] + df["puyuh"]

            # Tampilkan tabel yang sudah terfilter
            st.dataframe(
                df.drop(columns=["id"], errors="ignore"),
                use_container_width=True,
                hide_index=True
            )

            # Buat file Excel dari data yang sudah terfilter saja
            excel = "rekap_telur_filter.xlsx"
            df.drop(columns=["id"], errors="ignore").to_excel(excel, index=False)

            with open(excel, "rb") as file:
                st.download_button(f"⬇ Download Excel ({tgl_mulai} s/d {tgl_selesai})", file, file_name=f"rekap_produksi_{tgl_mulai}_to_{tgl_selesai}.xlsx")
        
        st.divider()
        st.subheader("🗑️ Hapus Data Produksi")
        
        pilihan_data = {
            row["id"]: f"{row['tanggal']} (Jam {row['jam']}) [🐔: {row['ayam']} | 🦆: {row['bebek']}]"
            for _, row in df_all.iterrows()
        }
        
        id_terpilih = st.selectbox(
            "Pilih baris data produksi yang ingin dihapus permanen:",
            options=list(pilihan_data.keys()),
            format_func=lambda x: pilihan_data[x]
        )
        
        if st.button("Hapus Permanen", type="primary"):
            conn.execute("DELETE FROM produksi WHERE id = ?", (id_terpilih,))
            conn.commit()
            st.success("Data produksi berhasil dihapus!")
            st.rerun()

# ==========================
# 4. DATA PENDAPATAN (DENGAN FILTER TANGGAL)
# ==========================

elif menu == "Data Pendapatan":
    st.subheader("💰 Laporan Pendapatan Keuangan (Omzet)")

    df_dana_all = pd.read_sql("SELECT tanggal, jam, ayam, bebek, puyuh FROM produksi", conn)
    # Jika database Anda sudah diperbaiki dari FROM, gunakan baris di bawah ini:
    df_dana_all = pd.read_sql("SELECT tanggal, jam, ayam, bebek, puyuh FROM produksi", conn)

    if df_dana_all.empty:
        st.info("Belum ada data transaksi keuangan.")
    else:
        df_dana_all = df_dana_all.sort_values(by="tanggal").reset_index(drop=True)

        # Tambahkan Filter Rentang Tanggal
        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal ", value=datetime.strptime(df_dana_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal ", value=datetime.strptime(df_dana_all["tanggal"].max(), "%Y-%m-%d").date())

        # Filter data berdasarkan tanggal
        df_dana_all["tanggal_dt"] = pd.to_datetime(df_dana_all["tanggal"]).dt.date
        df_dana = df_dana_all[(df_dana_all["tanggal_dt"] >= tgl_mulai) & (df_dana_all["tanggal_dt"] <= tgl_selesai)].copy()
        df_dana = df_dana.drop(columns=["tanggal_dt"])

        if df_dana.empty:
            st.info("Tidak ada data pendapatan pada rentang tanggal tersebut.")
        else:
            df_dana["Uang Ayam (Rp)"] = df_dana["ayam"] * HARGA_AYAM
            df_dana["Uang Bebek (Rp)"] = df_dana["bebek"] * HARGA_BEBEK
            df_dana["Uang Puyuh (Rp)"] = df_dana["puyuh"] * HARGA_PUYUH
            df_dana["Total Pendapatan (Rp)"] = (
                df_dana["Uang Ayam (Rp)"] + 
                df_dana["Uang Bebek (Rp)"] + 
                df_dana["Uang Puyuh (Rp)"]
            )

            df_tabel_uang = df_dana.drop(columns=["ayam", "bebek", "puyuh"]).sort_values(by="tanggal", ascending=False)

            # Tampilkan tabel terfilter
            st.dataframe(df_tabel_uang, use_container_width=True, hide_index=True)

            # Download data terfilter
            excel_keuangan = "rekap_pendapatan_filter.xlsx"
            df_tabel_uang.to_excel(excel_keuangan, index=False)

            with open(excel_keuangan, "rb") as file_keuangan:
                st.download_button(f"⬇ Download Excel ({tgl_mulai} s/d {tgl_selesai})", file_keuangan, file_name=f"rekap_pendapatan_{tgl_mulai}_to_{tgl_selesai}.xlsx")

            st.divider()
            st.subheader("📊 Grafik Distribusi Keuangan Harian")

            fig_dana = px.line(
                df_dana,
                x="tanggal",
                y=["Uang Ayam (Rp)", "Uang Bebek (Rp)", "Uang Puyuh (Rp)", "Total Pendapatan (Rp)"],
                markers=True,
                title="Tren Pendapatan Omzet Rupiah",
                color_discrete_map={
                    "Uang Ayam (Rp)": "#8B4513",
                    "Uang Bebek (Rp)": "#87CEFA",
                    "Uang Puyuh (Rp)": "#D3D3D3",
                    "Total Pendapatan (Rp)": "#00FF00"
                }
            )
            fig_dana.update_layout(template="plotly_white")
            st.plotly_chart(fig_dana, use_container_width=True)

# ==========================
# 5. DATA PENGELUARAN (DENGAN FILTER TANGGAL)
# ==========================

elif menu == "Data Pengeluaran":
    st.subheader("💸 Laporan Pengeluaran Operasional / Pembelian Pakan")

    df_keluar_all = pd.read_sql("SELECT id, tanggal, jam, keterangan, jumlah AS 'Jumlah (Rp)' FROM pengeluaran ORDER BY tanggal DESC", conn)

    if df_keluar_all.empty:
        st.info("Belum ada catatan pengeluaran biaya.")
    else:
        # Tambahkan Filter Rentang Tanggal
        st.write("🔍 **Filter Rentang Tanggal Download & Cetak:**")
        col_tgl1, col_tgl2 = st.columns(2)
        
        with col_tgl1:
            tgl_mulai = st.date_input("Dari Tanggal  ", value=datetime.strptime(df_keluar_all["tanggal"].min(), "%Y-%m-%d").date())
        with col_tgl2:
            tgl_selesai = st.date_input("Sampai Tanggal  ", value=datetime.strptime(df_keluar_all["tanggal"].max(), "%Y-%m-%d").date())

        # Filter data berdasarkan tanggal
        df_keluar_all["tanggal_dt"] = pd.to_datetime(df_keluar_all["tanggal"]).dt.date
        df_keluar_filtered = df_keluar_all[(df_keluar_all["tanggal_dt"] >= tgl_mulai) & (df_keluar_all["tanggal_dt"] <= tgl_selesai)].copy()
        df_keluar_filtered = df_keluar_filtered.drop(columns=["tanggal_dt"])

        if df_keluar_filtered.empty:
            st.info("Tidak ada data pengeluaran pada rentang tanggal tersebut.")
        else:
            # Tampilkan tabel terfilter
            st.dataframe(
                df_keluar_filtered.drop(columns=["id"], errors="ignore"),
                use_container_width=True,
                hide_index=True
            )

            # Download data terfilter
            excel_keluar = "rekap_pengeluaran_filter.xlsx"
            df_keluar_filtered.drop(columns=["id"], errors="ignore").to_excel(excel_keluar, index=False)

            with open(excel_keluar, "rb") as file_keluar:
                st.download_button(f"⬇ Download Excel ({tgl_mulai} s/d {tgl_selesai})", file_keluar, file_name=f"rekap_pengeluaran_{tgl_mulai}_to_{tgl_selesai}.xlsx")

        st.divider()
        st.subheader("🗑️ Hapus Nota Pengeluaran")

        pilihan_keluar = {
            row["id"]: f"{row['tanggal']} (Jam {row['jam']}) — {row['keterangan']} [Rp {row['Jumlah (Rp)']:,}]"
            for _, row in df_keluar_all.iterrows()
        }

        id_keluar_terpilih = st.selectbox(
            "Pilih nota pengeluaran yang ingin dihapus:",
            options=list(pilihan_keluar.keys()),
            format_func=lambda x: pilihan_keluar[x]
        )

        if st.button("Hapus Nota", type="primary"):
            conn.execute("DELETE FROM pengeluaran WHERE id = ?", (id_keluar_terpilih,))
            conn.commit()
            st.success("Nota pengeluaran berhasil dihapus!")
            st.rerun()
