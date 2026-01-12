import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="AI Script Auditor MBG", layout="wide")

@st.cache_data
def load_data():
    tkpi = pd.read_csv("data/clean_data.csv", engine="python")
    protein_cat = pd.read_csv("data/category_protein.csv")
    food_cat = pd.read_csv("data/food_category.csv")
    group_df = pd.read_csv("data/group.csv")
    standar_df = pd.read_csv("data/standar_mbg.csv", sep=";")
    return tkpi, protein_cat, food_cat, group_df, standar_df

tkpi_df, protein_cat_df, food_cat_df, group_df, standar_df = load_data()

def to_float(val):
    try:
        return float(str(val).replace(",", "."))
    except:
        return 0.0

# normalisasi
def normalize_food_name(raw_name, food_cat_df):
    text = raw_name.lower()
    for _, row in food_cat_df.iterrows():
        if row["nama bahan"].lower() in text:
            return row["nama bahan"]
    return raw_name

# kelas
def resolve_group(age, gender, group_df):
    df = group_df[
        (group_df["age_min"] <= age) &
        (group_df["age_max"] >= age) &
        ((group_df["gender"] == gender) | (group_df["gender"] == "all"))
    ]
    if df.empty:
        raise ValueError("Group MBG tidak ditemukan")
    return df.iloc[0]["group_id"]

# kalkulasi nutrisi
def calculate_menu_nutrition(menu_items, tkpi_df, protein_cat_df):
    total = {
        "energy": 0.0,
        "protein": 0.0,
        "animal_protein": 0.0,
        "fiber": 0.0,
        "carbohydrate": 0.0
    }

    for item in menu_items:
        name = item["food"]
        gram = item["gram"]

        row = tkpi_df[tkpi_df["nama"].str.contains(name, case=False, na=False)]
        if row.empty:
            continue

        row = row.iloc[0]
        factor = gram / 100

        energy = to_float(row["energi_kkal"]) * factor
        protein = to_float(row["protein_g"]) * factor
        fiber = to_float(row["serat_g"]) * factor
        carb = to_float(row["karbo_g"]) * factor

        total["energy"] += energy
        total["protein"] += protein
        total["fiber"] += fiber
        total["carbohydrate"] += carb

        prot = protein_cat_df[
            protein_cat_df["nama"].str.contains(name, case=False, na=False)
        ]
        if not prot.empty and str(prot.iloc[0]["is_animal"]).upper() == "TRUE":
            total["animal_protein"] += protein

    return total

# MBG evaluasi
def evaluate_mbg(nutrition, standard):
    return {
        "energy": standard["min_energy_kcal"] <= nutrition["energy"] <= standard["max_energy_kcal"],
        "protein": nutrition["protein"] >= standard["min_protein_g"],
        "animal_protein": nutrition["animal_protein"] >= standard["min_animal_protein_g"],
        "fiber": nutrition["fiber"] >= standard["min_fiber_g"],
        "carbohydrate": nutrition["carbohydrate"] >= standard["min_carbohydrate_g"],
    }

st.title("🍽️ MBG Support")

st.header("Profil Siswa")
age = st.number_input("Usia", min_value=4, max_value=18, step=1)
gender = st.selectbox("Jenis Kelamin", ["male", "female"])

st.header("Input Menu")
menu_items = []

for i in range(5):
    col1, col2 = st.columns(2)
    with col1:
        food = st.text_input(f"Makanan {i+1}")
    with col2:
        gram = st.number_input(f"Gram {i+1}", min_value=0, step=10)

    if food and gram > 0:
        normalized = normalize_food_name(food, food_cat_df)
        menu_items.append({"food": normalized, "gram": gram})

# output evaluasi
if st.button("Evaluasi Menu"):
    try:
        group_id = resolve_group(age, gender, group_df)
        standard = standar_df[standar_df["group_id"] == group_id].iloc[0]

        nutrition = calculate_menu_nutrition(menu_items, tkpi_df, protein_cat_df)
        evaluation = evaluate_mbg(nutrition, standard)

        score = sum(evaluation.values())
        if score == len(evaluation):
            status = "✅ SESUAI"
        elif score >= 3:
            status = "⚠️ PERLU PERBAIKAN"
        else:
            status = "❌ TIDAK SESUAI"

        st.subheader("Hasil Evaluasi")
        st.write(f"**Group MBG:** {group_id}")
        st.write(f"**Status:** {status}")
        st.json(nutrition)
        st.json(evaluation)

    except Exception as e:
        st.error(str(e))
