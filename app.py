import streamlit as st
import pandas as pd
import plotly.express as px

from logic.nutrition import perhitungan_nutrisi, aggregate
from logic.mbg import group_age, group_up, get_standard, evaluasi_mbg


st.set_page_config(
    page_title="MBG Menu Evaluator",
    layout="wide"
)


st.markdown("""
<style>
.card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 6px 14px rgba(0,0,0,0.06);
}
.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1.25rem;
}
.label {
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 6px;
    display: block;
}
</style>
""", unsafe_allow_html=True)


def load_csv_safe(path, delimiter=None):
    df = pd.read_csv(
        path,
        delimiter=delimiter or None,
        engine="python",
        encoding="utf-8-sig",
        on_bad_lines="warn"
    )
    df.columns = [
        col.strip().strip('"').replace(" ", "_").lower()
        for col in df.columns
    ]
    return df

tkpi = load_csv_safe("data/clean_data.csv")
food_cat = load_csv_safe("data/food_category.csv")
age_df = load_csv_safe("data/age_group.csv")
edu_df = load_csv_safe("data/education_level.csv")
std_df = load_csv_safe("data/standar_mbg.csv")


if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "student_info" not in st.session_state:
    st.session_state.student_info = {
        "jenjang": "",
        "kelas": "",
        "gender": ""
    }

kelas_options = {
    "SD": [
        "SD Kelas I", "SD Kelas II", "SD Kelas III",
        "SD Kelas IV", "SD Kelas V", "SD Kelas VI"
    ],
    "SMP": [
        "SMP Kelas VII", "SMP Kelas VIII", "SMP Kelas IX"
    ],
    "SMA": [
        "SMA Kelas X", "SMA Kelas XI", "SMA Kelas XII"
    ]
}

def kelas_to_age(kelas: str):
    mapping = {
        "SD Kelas I": 7,
        "SD Kelas II": 8,
        "SD Kelas III": 9,
        "SD Kelas IV": 10,
        "SD Kelas V": 11,
        "SD Kelas VI": 12,
        "SMP Kelas VII": 13,
        "SMP Kelas VIII": 14,
        "SMP Kelas IX": 15,
        "SMA Kelas X": 16,
        "SMA Kelas XI": 17,
        "SMA Kelas XII": 18,
    }
    return mapping.get(kelas, 7)


gender_map = {
    "Laki-laki": "male",
    "Perempuan": "female",
    "Semua": "all"
}

st.title("🍱 MBG Menu Evaluator")


# data input
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Informasi Siswa</div>', unsafe_allow_html=True)

    # Jenjang
    st.markdown('<label class="label">Jenjang Pendidikan</label>', unsafe_allow_html=True)
    jenjang = st.selectbox(
        "",
        ["", "SD", "SMP", "SMA"],
        key="jenjang_select"
    )

    # default gender sd
    if jenjang == "SD":
        st.session_state.student_info["gender"] = "Semua"

    # Kelas
    st.markdown('<label class="label">Kelas</label>', unsafe_allow_html=True)
    kelas = st.selectbox(
        "",
        [""] + kelas_options.get(jenjang, []),
        disabled=(jenjang == ""),
        key="kelas_select"
    )

    # Gender
    st.markdown('<label class="label">Jenis Kelamin</label>', unsafe_allow_html=True)
    gender = st.selectbox(
        "",
        ["Semua"] if jenjang == "SD" else ["", "Perempuan", "Laki-laki", "Semua"],
        disabled=(jenjang == "SD"),
        key="gender_select"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.student_info.update({
        "jenjang": jenjang,
        "kelas": kelas,
        "gender": gender
    })


# menu mbg
st.subheader("🍽️ Pilih Menu")

food_list = sorted(tkpi["nama"].unique())
food_name = st.selectbox("Nama Makanan", food_list)

gram = st.number_input("Berat (gram)", min_value=1.0, value=100.0, step=5.0)

if st.button("➕ Tambah ke Menu"):
    row = tkpi[tkpi["nama"] == food_name]
    if row.empty:
        st.error("Makanan tidak ditemukan")
        st.stop()

    food_id = str(row.iloc[0]["id"])
    nutrition = perhitungan_nutrisi(
        food_id=food_id,
        gram=gram,
        clean_df=tkpi,
        category_df=food_cat
    )

    st.session_state.menu_items.append(nutrition)
    st.success(f"{food_name} ({gram:.0f} g) ditambahkan")


if st.button("🔄 Reset Menu"):
    st.session_state.menu_items = []
    st.rerun()


# evaluasi
if st.session_state.menu_items and st.session_state.student_info["kelas"]:

    age = kelas_to_age(st.session_state.student_info["kelas"])
    gender_ui = st.session_state.student_info["gender"]
    gender = gender_map.get(gender_ui, "all")

    level, grade, default_gender = group_age(age, age_df)
    effective_gender = gender if gender != "all" else default_gender

    group_id = group_up(level, grade, edu_df, effective_gender)
    std = get_standard(group_id, std_df)

    total = aggregate(st.session_state.menu_items)
    result = evaluasi_mbg(total, std)

    st.divider()
    st.subheader("📊 Hasil Evaluasi Gizi")

    col1, col2, col3 = st.columns(3)
    col1.metric("Energi (kcal)", f"{total['energy']:.1f}", result["energy_status"])
    col2.metric("Protein (g)", f"{total['protein']:.1f}", "OK" if result["protein_ok"] else "Kurang")
    col3.metric("Serat (g)", f"{total['fiber']:.1f}", "OK" if result["fiber_ok"] else "Kurang")

    fig = px.bar(
        x=["Energi", "Protein", "Karbohidrat", "Serat"],
        y=[
            total["energy"],
            total["protein"],
            total["carbohydrate"],
            total["fiber"]
        ],
        title="Total Asupan Gizi"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📄 Detail Evaluasi (JSON)"):
        st.json({
            "group_id": group_id,
            "total": total,
            "evaluation": result
        })

else:
    st.info("Lengkapi informasi siswa dan menu terlebih dahulu.")
