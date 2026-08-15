import streamlit as st
import pandas as pd
import plotly.express as px
from database import supabase
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
# FUNGSI AMBIL DATA
# ==========================

def ambil_data():
    response = (
        supabase
        .table("produksi")
        .select("*")
        .order("tanggal", desc=True)
        .execute()
    )

    data = response.data

    if not data:
        return pd.DataFrame(
            columns=[
                "id",
                "tanggal",
                "ayam",
                "bebek",
                "puyuh"
            ]
        )

    return pd.DataFrame(data)


# ==========================
# DASHBOARD
# ==========================

if menu == "Dashboard":

    df = ambil_data()

    if df.empty:

        st.info("Belum ada data.")

    else:

        total_ayam = int(df["ayam"].sum())
        total_bebek = int(df["bebek"].sum())
        total_puyuh = int(df["puyuh"].sum())

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🐔 Telur Ayam",
            f"{total_ayam:,} Butir"
        )

        c2.metric(
            "🦆 Telur Bebek",
            f"{total_bebek:,} Butir"
        )

        c3.metric(
            "🐦 Telur Puyuh",
            f"{total_puyuh:,} Butir"
        )

        st.divider()

        fig = px.line(
            df.sort_values("tanggal"),
            x="tanggal",
            y=[
                "ayam",
                "bebek",
                "puyuh"
            ],
            markers=True,
            title="Grafik Produksi"
        )

        fig.update_layout(
            xaxis_title="Tanggal",
            yaxis_title="Jumlah Telur",
            legend_title="Jenis Telur"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ==========================
# INPUT PRODUKSI
# ==========================

elif menu == "Input Produksi":

    st.subheader("Input Produksi Harian")

    tanggal = st.date_input(
        "Tanggal",
        value=datetime.now().date()
    )

    ayam = st.number_input(
        "Telur Ayam",
        min_value=0,
        value=0,
        step=1
    )

    bebek = st.number_input(
        "Telur Bebek",
        min_value=0,
        value=0,
        step=1
    )

    puyuh = st.number_input(
        "Telur Puyuh",
        min_value=0,
        value=0,
        step=1
    )

    if st.button("Simpan", type="primary"):

        try:

            # Cek apakah tanggal sudah ada
            cek = (
                supabase
                .table("produksi")
                .select("id")
                .eq("tanggal", str(tanggal))
                .execute()
            )

            if cek.data:

                st.warning(
                    "Data untuk tanggal tersebut sudah ada."
                )

            else:

                response = (
                    supabase
                    .table("produksi")
                    .insert({
                        "tanggal": str(tanggal),
                        "ayam": ayam,
                        "bebek": bebek,
                        "puyuh": puyuh
                    })
                    .execute()
                )

                if response.data:

                    st.success(
                        "✅ Data berhasil disimpan."
                    )

                    st.rerun()

        except Exception as e:

            st.error(
                f"❌ Gagal menyimpan data: {e}"
            )


# ==========================
# DATA PRODUKSI
# ==========================

elif menu == "Data Produksi":

    df = ambil_data()

    if df.empty:

        st.warning("Belum ada data.")

    else:

        df["Total"] = (
            df["ayam"]
            + df["bebek"]
            + df["puyuh"]
        )

        # ==========================
        # TABEL
        # ==========================

        st.dataframe(
            df.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

        # ==========================
        # EXCEL
        # ==========================

        excel = "rekap_telur.xlsx"

        df.drop(
            columns=["id"],
            errors="ignore"
        ).to_excel(
            excel,
            index=False
        )

        with open(excel, "rb") as file:

            st.download_button(
                "⬇ Download Excel",
                file,
                file_name=excel
            )

        st.divider()

        # ==========================
        # EDIT / HAPUS
        # ==========================

        st.subheader(
            "🛠️ Manajemen Data"
        )

        pilihan_data = {
            int(row["id"]):
            f"ID {row['id']} — "
            f"{row['tanggal']} "
            f"[🐔: {row['ayam']} | "
            f"🦆: {row['bebek']} | "
            f"🐦: {row['puyuh']}]"
            for _, row in df.iterrows()
        }

        id_terpilih = st.selectbox(
            "Pilih data yang ingin dimodifikasi:",
            options=list(
                pilihan_data.keys()
            ),
            format_func=lambda x:
            pilihan_data[x]
        )

        data_lama = df[
            df["id"] == id_terpilih
        ].iloc[0]

        col_edit, col_hapus = st.columns(2)

        # ==========================
        # EDIT
        # ==========================

        with col_edit:

            with st.expander("📝 Edit Data"):

                with st.form("form_edit"):

                    tanggal_default = pd.to_datetime(
                        data_lama["tanggal"]
                    ).date()

                    edit_tanggal = st.date_input(
                        "Ubah Tanggal",
                        value=tanggal_default
                    )

                    edit_ayam = st.number_input(
                        "Ubah Telur Ayam",
                        min_value=0,
                        value=int(data_lama["ayam"]),
                        step=1
                    )

                    edit_bebek = st.number_input(
                        "Ubah Telur Bebek",
                        min_value=0,
                        value=int(data_lama["bebek"]),
                        step=1
                    )

                    edit_puyuh = st.number_input(
                        "Ubah Telur Puyuh",
                        min_value=0,
                        value=int(data_lama["puyuh"]),
                        step=1
                    )

                    tombol_simpan = st.form_submit_button(
                        "Simpan Perubahan"
                    )

                    if tombol_simpan:

                        try:

                            # Cek tanggal baru
                            cek = (
                                supabase
                                .table("produksi")
                                .select("id")
                                .eq(
                                    "tanggal",
                                    str(edit_tanggal)
                                )
                                .neq(
                                    "id",
                                    int(id_terpilih)
                                )
                                .execute()
                            )

                            if cek.data:

                                st.error(
                                    "Tanggal tersebut sudah memiliki data."
                                )

                            else:

                                response = (
                                    supabase
                                    .table("produksi")
                                    .update({
                                        "tanggal":
                                            str(edit_tanggal),
                                        "ayam":
                                            edit_ayam,
                                        "bebek":
                                            edit_bebek,
                                        "puyuh":
                                            edit_puyuh
                                    })
                                    .eq(
                                        "id",
                                        int(id_terpilih)
                                    )
                                    .execute()
                                )

                                if response.data:

                                    st.success(
                                        "✅ Data berhasil diperbarui!"
                                    )

                                    st.rerun()

                        except Exception as e:

                            st.error(
                                f"❌ Gagal memperbarui data: {e}"
                            )

        # ==========================
        # HAPUS
        # ==========================

        with col_hapus:

            with st.expander("🗑️ Hapus Data"):

                st.warning(
                    f"Apakah Anda yakin ingin "
                    f"menghapus data ID "
                    f"{id_terpilih} tanggal "
                    f"{data_lama['tanggal']}?"
                )

                tombol_hapus = st.button(
                    "Ya, Hapus Permanen",
                    type="primary"
                )

                if tombol_hapus:

                    try:

                        response = (
                            supabase
                            .table("produksi")
                            .delete()
                            .eq(
                                "id",
                                int(id_terpilih)
                            )
                            .execute()
                        )

                        if response.data:

                            st.success(
                                "✅ Data berhasil dihapus!"
                            )

                            st.rerun()

                    except Exception as e:

                        st.error(
                            f"❌ Gagal menghapus data: {e}"
                        )
