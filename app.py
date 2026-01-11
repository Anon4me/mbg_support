import streamlit as st
import plotly.express as px

from logic.loader import load_csv
from logic.nutrition import calculate_nutrition, aggregate
from logic.mbg import resolve_age, resolve_group, get_standard, evaluate_mbg

tkpi = load_csv("data/clean_data.csv")
food_cat = load_csv("data/food_category.csv")
age_df = load_csv("data/age_group.csv")
edu_df = load_csv("data/education_level.csv")
std_df = load_csv("data/standar_mbg.csv")

st.title("MBG Menu Evaluator")

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

# data input
with st.sidebar:
    st.header("Profil Penerima")
    age = st.number_input("Usia (tahun)", min_value=3, max_value=18, value=7)
    gender = st.selectbox("Gender", ["male", "female", "all"])

# menu mbg
st.subheader("Pilih Menu")

food_list = sorted(tkpi["nama_bahan"].unique())
food_name = st.selectbox("Nama Makanan", food_list)

gram = st.number_input(
    "Berat (gram)",
    min_value=1.0,
    value=100.0,
    step=5.0
)

if st.button("Tambah ke Menu"):
    row = tkpi[tkpi["nama_bahan"] == food_name]

    if row.empty:
        st.error("Makanan tidak ditemukan di database")
        st.stop()

    food_id = int(row.iloc[0]["id"])

    nutrition = calculate_nutrition(
        food_id=food_id,
        gram=gram,
        clean_df=tkpi,
        category_df=food_cat
    )

    st.session_state.menu_items.append(nutrition)
    st.success(f"Ditambahkan: {food_name} ({gram:.0f} g)")

if st.button("Reset Menu"):
    st.session_state.menu_items = []
    st.rerun()

# evaluasi
if st.session_state.menu_items:
    level, grade, default_gender = resolve_age(age, age_df)
    effective_gender = gender if gender != "all" else default_gender

    group_id = resolve_group(level, grade, edu_df, effective_gender)
    std = get_standard(group_id, std_df)

    total = aggregate(st.session_state.menu_items)
    result = evaluate_mbg(total, std)

    st.divider()
    st.subheader("Hasil Evaluasi Gizi")

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

    with st.expander("Detail Evaluasi (JSON)"):
        st.json({
            "group_id": group_id,
            "total": total,
            "evaluation": result
        })
else:
    st.info("Belum ada menu yang ditambahkan.")
