import streamlit as st
import pandas as pd
import plotly.express as px

from logic.nutrition import calculate_nutrition, aggregate
from logic.mbg import group_age, group_up, get_standard, evaluasi_mbg

def load_csv_safe(path, delimiter=None):
    df = pd.read_csv(
        path,
        delimiter=delimiter or None,
        engine='python',
        encoding='utf-8-sig',
        on_bad_lines='warn'
    )
    df.columns = [col.strip().strip('"').replace(" ", "_").lower() for col in df.columns]
    return df

tkpi = load_csv_safe("data/clean_data.csv")
food_cat = load_csv_safe("data/food_category.csv")
age_df = load_csv_safe("data/age_group.csv")
edu_df = load_csv_safe("data/education_level.csv")
std_df = load_csv_safe("data/standar_mbg.csv")

st.title("MBG Menu Evaluator")

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

with st.sidebar:
    st.header("Profil Penerima")
    age = st.number_input("Usia (tahun)", min_value=3, max_value=18, value=7)
    gender = st.selectbox("Gender", ["male", "female", "all"])

st.subheader("Pilih Menu")

food_list = sorted(tkpi["nama"].unique())
food_name = st.selectbox("Nama Makanan", food_list)

gram = st.number_input("Berat (gram)", min_value=1.0, value=100.0, step=5.0)

if st.button("Tambah ke Menu"):
    row = tkpi[tkpi["nama"] == food_name]
    if row.empty:
        st.error("Makanan tidak ditemukan di database")
        st.stop()
    food_id = str(row.iloc[0]["id"])
    nutrition = calculate_nutrition(food_id=food_id, gram=gram, clean_df=tkpi, category_df=food_cat)
    st.session_state.menu_items.append(nutrition)
    st.success(f"Ditambahkan: {food_name} ({gram:.0f} g)")

if st.button("Reset Menu"):
    st.session_state.menu_items = []
    st.rerun()

if st.session_state.menu_items:
    level, grade, default_gender = group_age(age, age_df)
    effective_gender = gender if gender != "all" else default_gender
    group_id = group_up(level, grade, edu_df, effective_gender)
    std = get_standard(group_id, std_df)
    total = aggregate(st.session_state.menu_items)
    result = evaluasi_mbg(total, std)

    st.divider()
    st.subheader("Hasil Evaluasi Gizi")

    col1, col2, col3 = st.columns(3)
    col1.metric("Energi (kcal)", f"{total['energy']:.1f}", result["energy_status"])
    col2.metric("Protein (g)", f"{total['protein']:.1f}", "OK" if result["protein_ok"] else "Kurang")
    col3.metric("Serat (g)", f"{total['fiber']:.1f}", "OK" if result["fiber_ok"] else "Kurang")

    fig = px.bar(
        x=["Energi", "Protein", "Karbohidrat", "Serat"],
        y=[total["energy"], total["protein"], total["carbohydrate"], total["fiber"]],
        title="Total Asupan Gizi"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Detail Evaluasi (JSON)"):
        st.json({"group_id": group_id, "total": total, "evaluation": result})
else:
    st.info("Belum ada menu yang ditambahkan.")
