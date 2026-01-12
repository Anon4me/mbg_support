import streamlit as st
import pandas as pd
import time
import uuid

st.set_page_config(page_title="AI Validasi Menu MBG", layout="wide")

# ===============================
# SESSION STATE
# ===============================
if "student_info" not in st.session_state:
    st.session_state.student_info = {"jenjang": "", "kelas": ""}

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "validated" not in st.session_state:
    st.session_state.validated = False

if "result" not in st.session_state:
    st.session_state.result = None

# ===============================
# CONSTANTS (UI TIDAK DIUBAH)
# ===============================
KELAS_OPTIONS = {
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

MENU_CATEGORIES = {
    "Makanan Pokok": [
        "Nasi Putih", "Nasi Merah", "Nasi Jagung",
        "Kentang Rebus", "Ubi Rebus", "Mie"
    ],
    "Lauk Pauk": [
        "Ayam Goreng", "Ayam Bakar", "Ikan Goreng",
        "Ikan Bakar", "Tempe Goreng", "Tahu Goreng",
        "Telur Rebus", "Telur Dadar"
    ],
    "Sayuran": [
        "Sayur Asem", "Sayur Sop", "Tumis Kangkung",
        "Capcay", "Sayur Lodeh"
    ],
    "Buah": [
        "Pisang", "Apel", "Jeruk", "Pepaya", "Semangka"
    ]
}

# ===============================
# DATA LOADER (FIXED)
# ===============================
@st.cache_data
def load_standar():
    df = pd.read_csv("data/mbg_standar.csv", sep=";")
    return df

# ===============================
# MBG LOGIC (FIXED TOTAL)
# ===============================
def resolve_group_id(jenjang, kelas):
    if jenjang == "SD":
        if any(k in kelas for k in ["I", "II", "III"]):
            return "SD_AWAL"
        return "SD_TINGGI"
    if jenjang == "SMP":
        return "SMP"
    if jenjang == "SMA":
        return "SMA"
    raise ValueError("Group MBG tidak valid")


def get_mbg_standard(jenjang, kelas, std_df):
    gid = resolve_group_id(jenjang, kelas)
    row = std_df[std_df["group_id"] == gid]

    if row.empty:
        raise ValueError(f"Standar MBG tidak ditemukan untuk {gid}")

    return row.iloc[0]

# ===============================
# UI HEADER
# ===============================
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Validasi otomatis menu sesuai standar gizi MBG")

# ===============================
# INFORMASI SISWA (DESIGN ASLI)
# ===============================
st.subheader("👤 Informasi Siswa")

info = st.session_state.student_info
col1, col2 = st.columns(2)

with col1:
    jenjang = st.selectbox(
        "Jenjang Pendidikan",
        ["", "SD", "SMP", "SMA"],
        index=["", "SD", "SMP", "SMA"].index(info["jenjang"]) if info["jenjang"] else 0
    )

if jenjang != info["jenjang"]:
    info["jenjang"] = jenjang
    info["kelas"] = ""

with col2:
    kelas = st.selectbox(
        "Kelas",
        ["Pilih Jenjang Terlebih Dahulu"]
        if not info["jenjang"]
        else [""] + KELAS_OPTIONS[info["jenjang"]],
        disabled=not info["jenjang"]
    )

    if kelas and kelas != "Pilih Jenjang Terlebih Dahulu":
        info["kelas"] = kelas

# ===============================
# MENU SELECTION (DESIGN ASLI)
# ===============================
st.subheader("🍴 Pilihan Menu Makanan")

for category, options in MENU_CATEGORIES.items():
    with st.expander(category):
        selected = st.multiselect(
            f"Pilih {category}",
            options,
            key=f"menu_{category}"
        )

        for item in selected:
            if not any(m["name"] == item for m in st.session_state.menu_items):
                st.session_state.menu_items.append({
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "name": item,
                    "portion": 100,
                    "custom": False
                })

# ===============================
# PORTION CONTROL (DESIGN ASLI)
# ===============================
st.subheader("⚖️ Kontrol Porsi")

if not st.session_state.menu_items:
    st.info("Pilih menu terlebih dahulu")
else:
    for item in st.session_state.menu_items:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{item['name']}**")
        item["custom"] = c2.checkbox(
            "Porsi Bebas",
            item["custom"],
            key=f"c_{item['id']}"
        )
        item["portion"] = c3.number_input(
            "gram",
            min_value=0,
            step=10,
            value=item["portion"],
            disabled=not item["custom"],
            key=f"p_{item['id']}"
        )

# ===============================
# VALIDATION (DESIGN ASLI)
# ===============================
st.subheader("✨ AI Validasi Menu")

can_validate = info["jenjang"] and info["kelas"] and st.session_state.menu_items

if st.button("Validasi Menu", disabled=not can_validate):
    with st.spinner("Memproses menu dengan AI..."):
        time.sleep(1)

    energi = sum(i["portion"] * 1.2 for i in st.session_state.menu_items)
    protein = sum(i["portion"] * 0.08 for i in st.session_state.menu_items)
    karbo = sum(i["portion"] * 0.2 for i in st.session_state.menu_items)
    serat = sum(i["portion"] * 0.03 for i in st.session_state.menu_items)

    has_protein = any(i["category"] == "Lauk Pauk" for i in st.session_state.menu_items)
    has_carb = any(i["category"] == "Makanan Pokok" for i in st.session_state.menu_items)
    has_veg = any(i["category"] == "Sayuran" for i in st.session_state.menu_items)
    has_fruit = any(i["category"] == "Buah" for i in st.session_state.menu_items)

    std_df = load_standar()
    std = get_mbg_standard(info["jenjang"], info["kelas"], std_df)

    checks = [
        std["min_energy_kcal"] <= energi <= std["max_energy_kcal"],
        protein >= std["min_protein_g"],
        karbo >= std["min_carbohydrate_g"],
        serat >= std["min_fiber_g"],
        has_protein,
        has_carb,
        has_veg,
        has_fruit
    ]

    status = "sesuai" if all(checks) else "tidak sesuai"

    st.session_state.result = {
        "energi": int(energi),
        "protein": int(protein),
        "karbohidrat": int(karbo),
        "serat": int(serat),
        "status": status
    }

    st.session_state.validated = True

# ===============================
# OUTPUT (DESIGN ASLI)
# ===============================
if st.session_state.validated:
    st.subheader("📊 Output Laporan Gizi")
    r = st.session_state.result

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Energi", f"{r['energi']} kkal")
    c2.metric("Protein", f"{r['protein']} g")
    c3.metric("Karbohidrat", f"{r['karbohidrat']} g")
    c4.metric("Serat", f"{r['serat']} g")

    if r["status"] == "sesuai":
        st.success("✅ Menu memenuhi standar gizi MBG")
    else:
        st.error("❌ Menu tidak memenuhi standar gizi MBG")
