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

    df = pd.read_sql("SELECT * FROM produksi", conn)

    if df.empty:
        st.info("Belum ada data.")
    else:
        # --- PERBAIKAN 1: Urutkan data berdasarkan tanggal agar grafik Dashboard rapi ---
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
# INPUT
# ==========================

elif menu == "Input Produksi":

    st.subheader("Input Produksi Harian")

    tanggal = st.date_input("Tanggal")

    ayam = st.number_input(
        "Telur Ayam (Butir)",
        min_value=0,
        value=0
    )

    bebek = st.number_input(
        "Telur Bebek (Butir)",
        min_value=0,
        value=0
    )

    puyuh = st.number_input(
        "Telur Puyuh (Butir)",
        min_value=0,
        value=0
    )

    if st.button("Simpan"):

        conn.execute(
            """
            INSERT INTO produksi
            (tanggal,ayam,bebek,puyuh)
            VALUES(?,?,?,?)
            """,
            (
                str(tanggal),
                ayam,
                bebek,
                puyuh
            )
        )

        conn.commit()

        st.success("Data berhasil disimpan.")

# ==========================
# DATA PRODUKSI (EDIT & HAPUS)
# ==========================

elif menu == "Data Produksi":

    df = pd.read_sql(
        "SELECT id, tanggal, ayam, bebek, puyuh FROM produksi ORDER BY tanggal DESC",
        conn
    )

    if df.empty:
        st.warning("Belum ada data.")
    else:

        df["Total"] = (
            df["ayam"] +
            df["bebek"] +
            df["puyuh"]
        )

        st.dataframe(
            df.drop(columns=["id"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        excel = "rekap_telur.xlsx"

        df.drop(columns=["id"], errors="ignore").to_excel(
            excel,
            index=False
        )

        with open(excel, "rb") as file:
            st.download_button(
                "⬇ Download Excel Produksi",
                file,
                file_name=excel
            )
        
        # --- BAGIAN EDIT DAN HAPUS DATA ---
        st.divider()
        st.subheader("🛠️ Manajemen Data (Edit / Hapus)")
        
        pilihan_data = {
            row["id"]: f"ID {row['id']} — {row['tanggal']} [🐔: {row['ayam']} | 🦆: {row['bebek']} | 🐦: {row['puyuh']}]"
            for _, row in df.iterrows()
        }
        
        id_terpilih = st.selectbox(
            "Pilih baris data yang ingin dimodifikasi:",
            options=list(pilihan_data.keys()),
            format_func=lambda x: pilihan_data[x]
        )
        
        data_lama = df[df["id"] == id_terpilih].iloc[0]
        
        col_edit, col_hapus = st.columns(2)
        
        with col_edit:
            with st.expander("📝 Edit Data"):
                with st.form("form_edit"):
                    tanggal_default = datetime.strptime(data_lama["tanggal"], "%Y-%m-%d").date()
                    
                    edit_tanggal = st.date_input("Ubah Tanggal", value=tanggal_default)
                    edit_ayam = st.number_input("Ubah Telur Ayam", min_value=0, value=int(data_lama["ayam"]))
                    edit_bebek = st.number_input("Ubah Telur Bebek", min_value=0, value=int(data_lama["bebek"]))
                    edit_puyuh = st.number_input("Ubah Telur Puyuh", min_value=0, value=int(data_lama["puyuh"]))
                    
                    tombol_simpan = st.form_submit_button("Simpan Perubahan")
                    
                    if tombol_simpan:
                        conn.execute(
                            """
                            UPDATE produksi
                            SET tanggal = ?, ayam = ?, bebek = ?, puyuh = ?
                            WHERE id = ?
                            """,
                            (str(edit_tanggal), edit_ayam, edit_bebek, edit_puyuh, id_terpilih)
                        )
                        conn.commit()
                        st.success("Data berhasil diperbarui!")
                        st.rerun()
                        
        with col_hapus:
            with st.expander("🗑️ Hapus Data"):
                st.warning(f"Apakah Anda yakin ingin menghapus data dengan ID {id_terpilih} tanggal {data_lama['tanggal']}?")
                tombol_hapus = st.button("Ya, Hapus Permanen", type="primary")
                
                if tombol_hapus:
                    conn.execute(
                        "DELETE FROM produksi WHERE id = ?",
                        (id_terpilih,)
                    )
                    conn.commit()
                    st.success("Data berhasil dihapus!")
                    st.rerun()

# ==========================
# DATA PENDAPATAN
# ==========================

elif menu == "Data Pendapatan":
    st.subheader("💰 Laporan Pendapatan Keuangan")

    df_dana = pd.read_sql(
        "SELECT tanggal, ayam, bebek, puyuh FROM produksi", 
        conn
    )

    if df_dana.empty:
        st.info("Belum ada data transaksi keuangan.")
    else:
        # --- PERBAIKAN 2: Urutkan data berdasarkan tanggal untuk tabel keuangan & grafik keuangan ---
        df_dana = df_dana.sort_values(by="tanggal").reset_index(drop=True)

        # Hitung Pendapatan per Baris Tanggal
        df_dana["Uang Ayam (Rp)"] = df_dana["ayam"] * HARGA_AYAM
        df_dana["Uang Bebek (Rp)"] = df_dana["bebek"] * HARGA_BEBEK
        df_dana["Uang Puyuh (Rp)"] = df_dana["puyuh"] * HARGA_PUYUH
        df_dana["Total Pendapatan (Rp)"] = (
            df_dana["Uang Ayam (Rp)"] + 
            df_dana["Uang Bebek (Rp)"] + 
            df_dana["Uang Puyuh (Rp)"]
        )

        # Buat salinan dataframe untuk tampilan tabel (diurutkan DESC agar data terbaru muncul paling atas)
        df_tabel_uang = df_dana.drop(columns=["ayam", "bebek", "puyuh"]).sort_values(by="tanggal", ascending=False)

        # Tampilkan tabel keuangan harian
        st.dataframe(
            df_tabel_uang,
            use_container_width=True,
            hide_index=True
        )

        # Tombol Download Keuangan khusus Excel
        excel_keuangan = "rekap_pendapatan.xlsx"
        df_tabel_uang.to_excel(excel_keuangan, index=False)

        with open(excel_keuangan, "rb") as file_keuangan:
            st.download_button(
                "⬇ Download Excel Pendapatan",
                file_keuangan,
                file_name=excel_keuangan
            )

        st.divider()
        st.subheader("📊 Grafik Distribusi Keuangan Harian")

        # Grafik Garis Keuangan (menggunakan df_dana asli yang ASCENDING agar grafik berjalan dari kiri ke kanan)
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
