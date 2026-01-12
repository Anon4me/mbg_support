import streamlit as st
import pandas as pd
import time
import uuid

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="AI Validasi Menu MBG", layout="wide")

# ======================================================
# SESSION STATE
# ======================================================
if "student_info" not in st.session_state:
    st.session_state.student_info = {"jenjang": "", "kelas": ""}

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "validated" not in st.session_state:
    st.session_state.validated = False

if "result" not in st.session_state:
    st.session_state.result = None

# ======================================================
# HARD-CODED MBG STANDARDS
# ======================================================
MBG = {
    "SD_AWAL":  {"min_e": 450, "max_e": 600, "min_p": 18, "min_pa": 8,  "min_f": 12, "min_c": 150},
    "SD_TINGGI":{"min_e": 500, "max_e": 700, "min_p": 22, "min_pa": 10, "min_f": 14, "min_c": 180},
    "SMP":      {"min_e": 600, "max_e": 850, "min_p": 26, "min_pa": 12, "min_f": 18, "min_c": 200},
    "SMA":      {"min_e": 700, "max_e": 900, "min_p": 28, "min_pa": 14, "min_f": 22, "min_c": 240},
}

# ======================================================
# OPTIONS
# ======================================================
KELAS_OPTIONS = {
    "SD": ["SD Kelas I","SD Kelas II","SD Kelas III","SD Kelas IV","SD Kelas V","SD Kelas VI"],
    "SMP": ["SMP Kelas VII","SMP Kelas VIII","SMP Kelas IX"],
    "SMA": ["SMA Kelas X","SMA Kelas XI","SMA Kelas XII"],
}

MENU_OPTIONS = [
    "Nasi Putih","Nasi Merah","Nasi Jagung","Kentang Rebus","Ubi Rebus","Mie",
    "Ayam Goreng","Ayam Bakar","Ikan Goreng","Ikan Bakar","Tempe Goreng",
    "Tahu Goreng","Telur Rebus","Telur Dadar",
    "Sayur Asem","Sayur Sop","Tumis Kangkung","Capcay","Sayur Lodeh",
    "Pisang","Apel","Jeruk","Pepaya","Semangka"
]

# ======================================================
# DATA LOADER
# ======================================================
@st.cache_data
def load_data():
    clean = pd.read_csv("data/clean_data.csv")
    food_cat = pd.read_csv("data/food_category.csv")
    protein_cat = pd.read_csv("data/category_protein.csv")

    clean.columns = clean.columns.str.lower()
    food_cat.columns = food_cat.columns.str.lower()
    protein_cat.columns = protein_cat.columns.str.lower()

    clean["nama"] = clean["nama"].str.lower().str.strip()
    food_cat["nama bahan"] = food_cat["nama bahan"].str.lower().str.strip()
    protein_cat["nama"] = protein_cat["nama"].str.lower().str.strip()

    return clean, food_cat, protein_cat

# ======================================================
# GROUP RESOLUTION
# ======================================================
def resolve_group(jenjang, kelas):
    if jenjang == "SD":
        return "SD_AWAL" if any(x in kelas for x in ["I","II","III"]) else "SD_TINGGI"
    return jenjang

# ======================================================
# NUTRITION CALCULATION
# ======================================================
def hitung_gizi(menu, clean_df):
    total = {"energi":0,"protein":0,"karbo":0,"serat":0}

    for m in menu:
        nama = m["name"].lower()
        porsi = m["portion"] / 100

        row = clean_df[clean_df["nama"] == nama]
        if row.empty:
            st.warning(f"Data gizi tidak ditemukan: {m['name']}")
            continue

        r = row.iloc[0]
        total["energi"] += r["energi_kkal"] * porsi
        total["protein"] += r["protein_g"] * porsi
        total["karbo"] += r["karbo_g"] * porsi
        total["serat"] += r["serat_g"] * porsi

    return total

def cek_kategori(menu, food_cat_df, target):
    foods = [m["name"].lower() for m in menu]
    return not food_cat_df[
        (food_cat_df["nama bahan"].isin(foods)) &
        (food_cat_df["kategori"] == target)
    ].empty

def hitung_protein_hewani(menu, clean_df, protein_df):
    total = 0
    for m in menu:
        nama = m["name"].lower()
        porsi = m["portion"] / 100

        if protein_df[
            (protein_df["nama"] == nama) &
            (protein_df["is_animal"] == True)
        ].empty:
            continue

        nut = clean_df[clean_df["nama"] == nama]
        if nut.empty:
            continue

        total += nut.iloc[0]["protein_g"] * porsi

    return total

# ======================================================
# UI
# ======================================================
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Perhitungan gizi real berbasis data")

st.subheader("👤 Informasi Siswa")
c1, c2 = st.columns(2)

with c1:
    jenjang = st.selectbox("Jenjang", ["","SD","SMP","SMA"])
with c2:
    kelas = st.selectbox("Kelas", [""] + KELAS_OPTIONS.get(jenjang, []), disabled=not jenjang)

st.subheader("🍴 Pilihan Menu")
selected = st.multiselect("Pilih Makanan", MENU_OPTIONS)

for s in selected:
    if not any(m["name"] == s for m in st.session_state.menu_items):
        st.session_state.menu_items.append({
            "id": str(uuid.uuid4()),
            "name": s,
            "portion": 100
        })

st.subheader("⚖️ Porsi")
for m in st.session_state.menu_items:
    m["portion"] = st.number_input(
        m["name"], 0, 500, m["portion"], step=10, key=m["id"]
    )

# ======================================================
# VALIDATION
# ======================================================
if st.button("Validasi Menu"):
    with st.spinner("Menghitung..."):
        time.sleep(1)

    clean_df, food_cat_df, protein_df = load_data()

    gizi = hitung_gizi(st.session_state.menu_items, clean_df)
    prot_hewani = hitung_protein_hewani(
        st.session_state.menu_items, clean_df, protein_df
    )

    group = resolve_group(jenjang, kelas)
    std = MBG[group]

    checks = [
        std["min_e"] <= gizi["energi"] <= std["max_e"],
        gizi["protein"] >= std["min_p"],
        prot_hewani >= std["min_pa"],
        gizi["karbo"] >= std["min_c"],
        gizi["serat"] >= std["min_f"],
        cek_kategori(st.session_state.menu_items, food_cat_df, "pokok"),
        cek_kategori(st.session_state.menu_items, food_cat_df, "lauk"),
        cek_kategori(st.session_state.menu_items, food_cat_df, "sayur"),
        cek_kategori(st.session_state.menu_items, food_cat_df, "buah"),
    ]

    st.session_state.result = {
        "energi": int(gizi["energi"]),
        "protein": int(gizi["protein"]),
        "karbo": int(gizi["karbo"]),
        "serat": int(gizi["serat"]),
        "status": "sesuai" if all(checks) else "tidak sesuai"
    }
    st.session_state.validated = True

# ======================================================
# OUTPUT
# ======================================================
if st.session_state.validated:
    r = st.session_state.result
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Energi", f"{r['energi']} kkal")
    c2.metric("Protein", f"{r['protein']} g")
    c3.metric("Karbohidrat", f"{r['karbo']} g")
    c4.metric("Serat", f"{r['serat']} g")

    if r["status"] == "sesuai":
        st.success("✅ Menu MEMENUHI standar MBG")
    else:
        st.error("❌ Menu TIDAK memenuhi standar MBG")
