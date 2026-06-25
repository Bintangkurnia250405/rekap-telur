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

st.title("🥚 Rekap Produksi Telur")

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Input Produksi",
        "Data Produksi"
    ]
)

# ==========================
# DASHBOARD
# ==========================

if menu == "Dashboard":

    df = pd.read_sql("SELECT * FROM produksi", conn)

    if df.empty:
        st.info("Belum ada data.")
    else:

        total_ayam = df["ayam"].sum()
        total_bebek = df["bebek"].sum()
        total_puyuh = df["puyuh"].sum()

        c1,c2,c3 = st.columns(3)

        c1.metric("🐔 Telur Ayam", total_ayam)
        c2.metric("🦆 Telur Bebek", total_bebek)
        c3.metric("🐦 Telur Puyuh", total_puyuh)

        HARGA_AYAM = 1500
        HARGA_BEBEK = 3000
        HARGA_PUYUH = 500
        
        total_harga_ayam = total_ayam * HARGA_AYAM
        total_harga_bebek = total_bebek * HARGA_BEBEK
        total_harga_puyuh = total_puyuh * HARGA_PUYUH
        
        grand_total = (
            total_harga_ayam +
            total_harga_bebek +
            total_harga_puyuh
        )

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
        "Telur Ayam",
        min_value=0,
        value=0
    )

    bebek = st.number_input(
        "Telur Bebek",
        min_value=0,
        value=0
    )

    puyuh = st.number_input(
        "Telur Puyuh",
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

    # Mengambil seluruh data termasuk kolom 'id' asli Anda
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

        # Tampilkan data ke user tanpa kolom 'id' agar terlihat rapi di tabel utama
        st.dataframe(
            df.drop(columns=["id"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )

        excel = "rekap_telur.xlsx"

        # Simpan ke Excel tanpa menyertakan kolom 'id'
        df.drop(columns=["id"], errors="ignore").to_excel(
            excel,
            index=False
        )

        with open(excel, "rb") as file:
            st.download_button(
                "⬇ Download Excel",
                file,
                file_name=excel
            )
        
        # --- BAGIAN EDIT DAN HAPUS DATA ---
        st.divider()
        st.subheader("🛠️ Manajemen Data (Edit / Hapus)")
        
        # Membuat opsi pilihan dropdown menggunakan kolom 'id' asli
        pilihan_data = {
            row["id"]: f"ID {row['id']} — {row['tanggal']} [🐔: {row['ayam']} | 🦆: {row['bebek']} | 🐦: {row['puyuh']}]"
            for _, row in df.iterrows()
        }
        
        id_terpilih = st.selectbox(
            "Pilih baris data yang ingin dimodifikasi:",
            options=list(pilihan_data.keys()),
            format_func=lambda x: pilihan_data[x]
        )
        
        # Mengambil data lama berdasarkan 'id' yang dipilih
        data_lama = df[df["id"] == id_terpilih].iloc[0]
        
        col_edit, col_hapus = st.columns(2)
        
        # --- Kolom Edit Data ---
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
                        
        # --- Kolom Hapus Data ---
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
