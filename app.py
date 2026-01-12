import streamlit as st
import pandas as pd
import uuid

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="AI Validasi Menu MBG", layout="wide")

# ===============================
# HARDCODE STANDAR MBG
# ===============================
MBG_STANDARD = {
    "SD_AWAL":  {"min_energy": 450, "max_energy": 600, "min_protein": 18, "min_animal": 8,  "min_fiber": 12, "min_carb": 150},
    "SD_TINGGI":{"min_energy": 500, "max_energy": 700, "min_protein": 22, "min_animal": 10, "min_fiber": 14, "min_carb": 180},
    "SMP":      {"min_energy": 600, "max_energy": 850, "min_protein": 26, "min_animal": 12, "min_fiber": 18, "min_carb": 200},
    "SMA":      {"min_energy": 700, "max_energy": 900, "min_protein": 28, "min_animal": 14, "min_fiber": 22, "min_carb": 240},
}

KELAS_MAP = {
    "SD Kelas I": "SD_AWAL",
    "SD Kelas II": "SD_AWAL",
    "SD Kelas III": "SD_AWAL",
    "SD Kelas IV": "SD_TINGGI",
    "SD Kelas V": "SD_TINGGI",
    "SD Kelas VI": "SD_TINGGI",
    "SMP Kelas VII": "SMP",
    "SMP Kelas VIII": "SMP",
    "SMP Kelas IX": "SMP",
    "SMA Kelas X": "SMA",
    "SMA Kelas XI": "SMA",
    "SMA Kelas XII": "SMA",
}

# ===============================
# SESSION STATE
# ===============================
if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "result" not in st.session_state:
    st.session_state.result = None

# ===============================
# LOAD DATA (FIX HEADER)
# ===============================
@st.cache_data
def load_data():
    clean = pd.read_csv("data/clean_data.csv", quotechar='"', skipinitialspace=True)
    food_cat = pd.read_csv("data/food_category.csv")
    protein = pd.read_csv("data/category_protein.csv")

    for df in [clean, food_cat, protein]:
        df.columns = df.columns.str.replace('"', '').str.strip().str.lower()

    clean["nama"] = clean["nama"].str.lower().str.strip()
    food_cat["nama"] = food_cat["nama"].str.lower().str.strip()
    food_cat["kategori"] = food_cat["kategori"].str.lower().str.strip()
    protein["nama"] = protein["nama"].str.lower().str.strip()

    return clean, food_cat, protein

clean_df, food_cat_df, protein_df = load_data()

# ===============================
# BUILD MENU BY CATEGORY
# ===============================

def normalize_category(cat):
    if "pokok" in cat:
        return "Makanan Pokok"
    if "lauk" in cat:
        return "Lauk Pauk"
    if "sayur" in cat:
        return "Sayuran"
    if "buah" in cat:
        return "Buah"
    return None

# ===============================
# BUILD MENU OPTIONS
# ===============================
MENU_OPTIONS = {
    "Makanan Pokok": [],
    "Lauk Pauk": [],
    "Sayuran": [],
    "Buah": []
}

for _, r in food_cat_df.iterrows():
    cat = normalize_category(r["kategori"])
    if cat:
        MENU_OPTIONS[cat].append(r["nama"])

# ===============================
# UI HEADER
# ===============================
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Perhitungan REAL berdasarkan data gizi")

# ===============================
# STUDENT INFO
# ===============================
st.subheader("👤 Informasi Siswa")
col1, col2 = st.columns(2)

with col1:
    jenjang = st.selectbox("Jenjang", ["SD", "SMP", "SMA"])

with col2:
    kelas = st.selectbox("Kelas", [k for k in KELAS_MAP if k.startswith(jenjang)])

std = MBG_STANDARD[KELAS_MAP[kelas]]

# ===============================
# MENU SELECTION
# ===============================
st.subheader("🍴 Pilihan Menu")

for category, options in MENU_OPTIONS.items():
    with st.expander(category):
        selected = st.multiselect(category, options)
        for item in selected:
            if not any(m["name"] == item for m in st.session_state.menu_items):
                st.session_state.menu_items.append({
                    "id": str(uuid.uuid4()),
                    "name": item,
                    "category": category,
                    "portion": 100
                })

# ===============================
# PORTION CONTROL
# ===============================
st.subheader("⚖️ Porsi")

for item in st.session_state.menu_items:
    c1, c2 = st.columns([3, 1])
    c1.write(item["name"])
    item["portion"] = c2.number_input(
        "gram",
        min_value=0,
        step=10,
        value=item["portion"],
        key=item["id"]
    )

# ===============================
# VALIDATION
# ===============================
if st.button("Validasi Menu"):
    energi = protein = serat = karbo = animal_protein = 0

    for item in st.session_state.menu_items:
        row = clean_df[clean_df["nama"] == item["name"].lower()]
        if row.empty:
            continue

        g = item["portion"] / 100
        energi += float(row["energi_kkal"].values[0]) * g
        protein += float(row["protein_g"].values[0]) * g
        karbo += float(row["karbo_g"].values[0]) * g
        serat += float(row["serat_g"].values[0]) * g

        p = protein_df[protein_df["nama"] == item["name"].lower()]
        if not p.empty and p["is_animal"].values[0]:
            animal_protein += row["protein_g"].values[0] * g

    status = (
        std["min_energy"] <= energi <= std["max_energy"]
        and protein >= std["min_protein"]
        and karbo >= std["min_carb"]
        and serat >= std["min_fiber"]
        and animal_protein >= std["min_animal"]
    )

    st.session_state.result = {
        "energi": int(energi),
        "protein": int(protein),
        "karbo": int(karbo),
        "serat": int(serat),
        "animal": int(animal_protein),
        "status": status
    }

# ===============================
# OUTPUT
# ===============================
if st.session_state.result:
    r = st.session_state.result
    st.subheader("📊 Hasil")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Energi", f"{r['energi']} kkal")
    c2.metric("Protein", f"{r['protein']} g")
    c3.metric("Protein Hewani", f"{r['animal']} g")
    c4.metric("Karbohidrat", f"{r['karbo']} g")
    c5.metric("Serat", f"{r['serat']} g")

    if r["status"]:
        st.success("✅ MENU SESUAI STANDAR MBG")
    else:
        st.error("❌ MENU TIDAK SESUAI STANDAR MBG")
