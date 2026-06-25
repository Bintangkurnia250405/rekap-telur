import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import conn
from datetime import datetime

st.set_page_config(
    page_title="Rekap Produksi Telur",
    page_icon="🥚",
    layout="wide"
)

st.title("🥚 Rekap Produksi & Pendapatan Telur")

# Pilihan menu
menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Input Produksi",
        "Data Produksi",
        "Data Pendapatan"
    ]
)

# Konstanta Harga Satuan Telur
HARGA_AYAM = 1500
HARGA_BEBEK = 3000
HARGA_PUYUH = 500

# ==========================
# DASHBOARD
# ==========================

if menu == "Dashboard":

    df = pd.read_sql("SELECT * FROMBox produksi", conn)

    if df.empty:
        st.info("Belum ada data.")
    else:
        # Urutkan data berdasarkan tanggal dari kiri ke kanan agar grafik rapi
        df = df.sort_values(by="tanggal").reset_index(drop=True)
        
        total_ayam = df["ayam"].sum()
        total_bebek = df["bebek"].sum()
        total_puyuh = df["puyuh"].sum()
        
        pendapatan_ayam = total_ayam * HARGA_AYAM
        pendapatan_bebek = total_bebek * HARGA_BEBEK
        pendapatan_puyuh = total_puyuh * HARGA_PUYUH
        
        grand_total = (
            pendapatan_ayam +
            pendapatan_bebek +
            pendapatan_puyuh
        )
        
        c1,c2,c3,c4 = st.columns(4)
        
        c1.metric("🐔 Telur Ayam", f"{total_ayam:,} butir")
        c2.metric("🦆 Telur Bebek", f"{total_bebek:,} butir")
        c3.metric("🐦 Telur Puyuh", f"{total_puyuh:,} butir")
        c4.metric("💰 Total Pendapatan", f"Rp {grand_total:,}")

        st.divider()

        df["Total"] = (
            df["ayam"] +
            df["bebek"] +
            df["puyuh"]
        )

        fig = px.line(
            df,
            x="tanggal",
            y=["ayam", "bebek", "puyuh"],
            markers=True,
            title="Grafik Tren Produksi Harian",
            color_discrete_map={
                "ayam": "#8B4513",     # Coklat
                "bebek": "#87CEFA",    # Biru muda
                "puyuh": "#D3D3D3"     # Abu muda
            }
        )
        
        fig.update_layout(
            legend_title="Jenis Telur",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ==========================
# INPUT (SISTEM PROTEKSI GANDA / OTOMATIS REDIRECT EDIT)
# ==========================

elif menu == "Input Produksi":

    st.subheader("Input / Edit Produksi Harian")

    tanggal = st.date_input("Pilih Tanggal")
    str_tanggal = str(tanggal)

    # Cek ke database apakah tanggal ini sudah pernah diisi
    cursor = conn.cursor()
    cursor.execute("SELECT ayam, bebek, puyuh FROM produksi WHERE tanggal = ?", (str_tanggal,))
    data_ada = cursor.fetchone()

    # Jika tanggal sudah ada, ambil nilai lamanya untuk dijadikan default pengisian
    if data_ada:
        st.warning(f"⚠️ Tanggal {str_tanggal} sudah memiliki data di database. Mengisi form ini akan langsung MEMPERBARUI data lama.")
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

    # Tombol dinamis tergantung status tanggal
    if data_ada:
        if st.button("🔄 Perbarui Data (Overwrite)", type="primary"):
            conn.execute(
                """
                UPDATE produksi 
                SET ayam = ?, bebek = ?, puyuh = ? 
                WHERE tanggal = ?
                """,
                (ayam, bebek, puyuh, str_tanggal)
            )
            conn.commit()
            st.success(f"Data tanggal {str_tanggal} berhasil diperbarui!")
            st.rerun()
    else:
        if st.button("📥 Simpan Data Baru"):
            conn.execute(
                """
                INSERT INTO produksi (tanggal, ayam, bebek, puyuh) 
                VALUES (?, ?, ?, ?)
                """,
                (str_tanggal, ayam, bebek, puyuh)
            )
            conn.commit()
            st.success("Data baru berhasil disimpan.")
            st.rerun()

# ==========================
# DATA PRODUKSI (HAPUS DATA)
# ==========================

elif menu == "Data Produksi":

    df = pd.read_sql(
        "SELECT id, tanggal, ayam, bebek, puyuh FROM produksi ORDER BY tanggal DESC",
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
        
        # Sederhanakan bagian bawah hanya untuk hapus data, karena edit sudah digabung ke menu Input!
        st.divider()
        st.subheader("🗑️ Hapus Data")
        
        pilihan_data = {
            row["id"]: f"{row['tanggal']} [🐔: {row['ayam']} | 🦆: {row['bebek']} | 🐦: {row['puyuh']}]"
            for _, row in df.iterrows()
        }
        
        id_terpilih = st.selectbox(
            "Pilih baris data yang ingin dihapus permanen:",
            options=list(pilihan_data.keys()),
            format_func=lambda x: pilihan_data[x]
        )
        
        if st.button("Hapus Permanen", type="primary"):
            conn.execute("DELETE FROM produksi WHERE id = ?", (id_terpilih,))
            conn.commit()
            st.success("Data berhasil dihapus!")
            st.rerun()

# ==========================
# DATA PENDAPATAN
# ==========================

elif menu == "Data Pendapatan":
    st.subheader("💰 Laporan Pendapatan Keuangan")

    df_dana = pd.read_sql("SELECT tanggal, ayam, bebek, puyuh FROM produksi", conn)

    if df_dana.empty:
        st.info("Belum ada data transaksi keuangan.")
    else:
        # Urutkan data berdasarkan tanggal agar grafik finansial maju teratur
        df_dana = df_dana.sort_values(by="tanggal").reset_index(drop=True)

        # Perhitungan finansial harian
        df_dana["Uang Ayam (Rp)"] = df_dana["ayam"] * HARGA_AYAM
        df_dana["Uang Bebek (Rp)"] = df_dana["bebek"] * HARGA_BEBEK
        df_dana["Uang Puyuh (Rp)"] = df_dana["puyuh"] * HARGA_PUYUH
        df_dana["Total Pendapatan (Rp)"] = (
            df_dana["Uang Ayam (Rp)"] + 
            df_dana["Uang Bebek (Rp)"] + 
            df_dana["Uang Puyuh (Rp)"]
        )

        # Tabel versi Descending (data terbaru paling atas)
        df_tabel_uang = df_dana.drop(columns=["ayam", "bebek", "puyuh"]).sort_values(by="tanggal", ascending=False)

        st.dataframe(df_tabel_uang, use_container_width=True, hide_index=True)

        excel_keuangan = "rekap_pendapatan.xlsx"
        df_tabel_uang.to_excel(excel_keuangan, index=False)

        with open(excel_keuangan, "rb") as file_keuangan:
            st.download_button("⬇ Download Excel Pendapatan", file_keuangan, file_name=excel_keuangan)

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
