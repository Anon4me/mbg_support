import streamlit as st
import pandas as pd
import uuid
from collections import defaultdict

st.set_page_config(page_title="AI Validasi Menu MBG", layout="wide")

MBG_STANDARD = {
    "SD_AWAL":  {"min_energy": 450, "max_energy": 600, "min_protein": 18, "min_animal": 8,  "min_fiber": 12, "min_carb": 75},
    "SD_TINGGI":{"min_energy": 500, "max_energy": 700, "min_protein": 22, "min_animal": 10, "min_fiber": 14, "min_carb": 90},
    "SMP":      {"min_energy": 600, "max_energy": 850, "min_protein": 24, "min_animal": 12, "min_fiber": 18, "min_carb": 115},
    "SMA":      {"min_energy": 700, "max_energy": 900, "min_protein": 26, "min_animal": 14, "min_fiber": 22, "min_carb": 130},
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

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "result" not in st.session_state:
    st.session_state.result = None

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

NUM_COLS = ["energi_kkal", "protein_g", "karbo_g", "serat_g"]

for col in NUM_COLS:
    clean_df[col] = (
        clean_df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce").fillna(0)

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

# data murid/siswa
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Perhitungan REAL berdasarkan data gizi")

st.subheader("👤 Informasi Siswa")
col1, col2 = st.columns(2)

with col1:
    jenjang = st.selectbox("Jenjang", ["SD", "SMP", "SMA"])

with col2:
    kelas = st.selectbox("Kelas", [k for k in KELAS_MAP if k.startswith(jenjang)])

std = MBG_STANDARD[KELAS_MAP[kelas]]

# menu makanan
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

# porsi input
def group_menu_by_category(menu_items):
    grouped = defaultdict(list)
    for m in menu_items:
        grouped[m["category"]].append(m)
    return grouped


def avg_nutrient_per_100g(df, names, col):
    rows = df[df["nama"].isin(names)]
    if rows.empty:
        return 0
    return rows[col].mean()

st.subheader("⚖️ Porsi per Kategori")

grouped_menu = defaultdict(list)
for item in st.session_state.menu_items:
    grouped_menu[item["category"]].append(item)

for category, items in grouped_menu.items():
    st.markdown(f"### 🍽️ {category}")

    for item in items:
        c1, c2 = st.columns([4, 1])
        c1.write(item["name"])
        item["portion"] = c2.number_input(
            "gram",
            min_value=0,
            step=10,
            value=item["portion"],
            key=item["id"]
        )


# validasi
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


# hasil output
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

# rekomendasi 
    st.divider()
    st.subheader("🧠 Rekomendasi Penyesuaian Menu")

    rekomendasi = []

    if r["energi"] > std["max_energy"]:
        rekomendasi.append("Kurangi porsi makanan pokok atau lauk tinggi lemak")
    elif r["energi"] < std["min_energy"]:
        rekomendasi.append("Tambahkan porsi makanan pokok")

    if r["karbo"] < std["min_carb"]:
        rekomendasi.append("Tambahkan sumber karbohidrat (nasi / kentang / jagung)")

    if r["protein"] < std["min_protein"]:
        rekomendasi.append("Tambahkan lauk berprotein (ayam, ikan, telur, tempe)")

    if r["animal"] < std["min_animal"]:
        rekomendasi.append("Tambahkan lauk protein hewani")

    if r["serat"] < std["min_fiber"]:
        rekomendasi.append("Tambahkan sayuran hijau atau buah")

    if rekomendasi:
        for rec in rekomendasi:
            st.info(rec)
    else:
        st.success("Menu sudah optimal, tidak perlu penyesuaian ✅")

# tabel gambaran nutrisi
    st.divider()
    st.subheader("📋 Kebutuhan Nutrisi untuk Menu Valid")

    def status_label(value, min_val=None, max_val=None):
        if min_val is not None and value < min_val:
            return "❌ Kurang"
        if max_val is not None and value > max_val:
            return "⚠️ Berlebih"
        return "✅ Cukup"

    df_kebutuhan = pd.DataFrame([
        {
            "Nutrisi": "Energi (kkal)",
            "Standar MBG": f"{std['min_energy']} – {std['max_energy']}",
            "Menu Saat Ini": r["energi"],
            "Selisih": (
                r["energi"] - std["min_energy"]
                if r["energi"] < std["min_energy"]
                else r["energi"] - std["max_energy"]
                if r["energi"] > std["max_energy"]
                else 0
            ),
            "Status": status_label(r["energi"], std["min_energy"], std["max_energy"]),
        },
        {
            "Nutrisi": "Protein (g)",
            "Standar MBG": f"≥ {std['min_protein']}",
            "Menu Saat Ini": r["protein"],
            "Selisih": r["protein"] - std["min_protein"],
            "Status": status_label(r["protein"], std["min_protein"]),
        },
        {
            "Nutrisi": "Protein Hewani (g)",
            "Standar MBG": f"≥ {std['min_animal']}",
            "Menu Saat Ini": r["animal"],
            "Selisih": r["animal"] - std["min_animal"],
            "Status": status_label(r["animal"], std["min_animal"]),
        },
        {
            "Nutrisi": "Karbohidrat (g)",
            "Standar MBG": f"≥ {std['min_carb']}",
            "Menu Saat Ini": r["karbo"],
            "Selisih": r["karbo"] - std["min_carb"],
            "Status": status_label(r["karbo"], std["min_carb"]),
        },
        {
            "Nutrisi": "Serat (g)",
            "Standar MBG": f"≥ {std['min_fiber']}",
            "Menu Saat Ini": r["serat"],
            "Selisih": r["serat"] - std["min_fiber"],
            "Status": status_label(r["serat"], std["min_fiber"]),
        },
    ])

    st.dataframe(df_kebutuhan, use_container_width=True, hide_index=True)
