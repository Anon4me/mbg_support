import streamlit as st
import time
import uuid

# ===============================
# PAGE CONFIG
# ===============================
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
# HARD-CODED CLASS OPTIONS
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

# ===============================
# HARD-CODED MBG STANDARDS
# ===============================
MBG_STANDARDS = {
    "SD_AWAL": {
        "min_energy": 450,
        "max_energy": 600,
        "min_protein": 18,
        "min_fiber": 12,
        "min_carb": 150,
        "req_protein": True,
        "req_carb": True,
        "req_veg": True,
        "req_fruit": True,
    },
    "SD_TINGGI": {
        "min_energy": 500,
        "max_energy": 700,
        "min_protein": 22,
        "min_fiber": 14,
        "min_carb": 180,
        "req_protein": True,
        "req_carb": True,
        "req_veg": True,
        "req_fruit": True,
    },
    "SMP": {
        "min_energy": 600,
        "max_energy": 850,
        "min_protein": 26,
        "min_fiber": 18,
        "min_carb": 200,
        "req_protein": True,
        "req_carb": True,
        "req_veg": True,
        "req_fruit": True,
    },
    "SMA": {
        "min_energy": 700,
        "max_energy": 900,
        "min_protein": 28,
        "min_fiber": 22,
        "min_carb": 240,
        "req_protein": True,
        "req_carb": True,
        "req_veg": True,
        "req_fruit": True,
    },
}

# ===============================
# MENU CATEGORIES
# ===============================
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
# GROUP RESOLUTION (HARDCODED)
# ===============================
def resolve_group_id(jenjang, kelas):
    if jenjang == "SD":
        if "I" in kelas or "II" in kelas or "III" in kelas:
            return "SD_AWAL"
        return "SD_TINGGI"
    return jenjang  # SMP / SMA

# ===============================
# UI HEADER
# ===============================
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Validasi otomatis menu sesuai standar gizi MBG")

# ===============================
# INFORMASI SISWA
# ===============================
st.subheader("👤 Informasi Siswa")

info = st.session_state.student_info
col1, col2 = st.columns(2)

with col1:
    jenjang = st.selectbox(
        "Jenjang Pendidikan",
        ["", "SD", "SMP", "SMA"]
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
# MENU SELECTION
# ===============================
st.subheader("🍴 Pilihan Menu Makanan")

for category, options in MENU_CATEGORIES.items():
    with st.expander(category):
        selected = st.multiselect(category, options)

        for item in selected:
            if not any(m["name"] == item for m in st.session_state.menu_items):
                st.session_state.menu_items.append({
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "name": item,
                    "portion": 100
                })

# ===============================
# PORTION CONTROL
# ===============================
st.subheader("⚖️ Kontrol Porsi")

for item in st.session_state.menu_items:
    c1, c2 = st.columns([4, 1])
    c1.markdown(f"**{item['name']}**")
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
st.subheader("✨ AI Validasi Menu")

can_validate = info["jenjang"] and info["kelas"] and st.session_state.menu_items

if st.button("Validasi Menu", disabled=not can_validate):
    with st.spinner("Memproses menu..."):
        time.sleep(1)

    energi = sum(i["portion"] * 1.2 for i in st.session_state.menu_items)
    protein = sum(i["portion"] * 0.08 for i in st.session_state.menu_items)
    karbo = sum(i["portion"] * 0.2 for i in st.session_state.menu_items)
    serat = sum(i["portion"] * 0.03 for i in st.session_state.menu_items)

    has_protein = any(i["category"] == "Lauk Pauk" for i in st.session_state.menu_items)
    has_carb = any(i["category"] == "Makanan Pokok" for i in st.session_state.menu_items)
    has_veg = any(i["category"] == "Sayuran" for i in st.session_state.menu_items)
    has_fruit = any(i["category"] == "Buah" for i in st.session_state.menu_items)

    group_id = resolve_group_id(info["jenjang"], info["kelas"])
    std = MBG_STANDARDS[group_id]

    checks = [
        std["min_energy"] <= energi <= std["max_energy"],
        protein >= std["min_protein"],
        karbo >= std["min_carb"],
        serat >= std["min_fiber"],
        has_protein,
        has_carb,
        has_veg,
        has_fruit
    ]

    st.session_state.result = {
        "energi": int(energi),
        "protein": int(protein),
        "karbo": int(karbo),
        "serat": int(serat),
        "status": "sesuai" if all(checks) else "tidak sesuai"
    }

    st.session_state.validated = True

# ===============================
# OUTPUT
# ===============================
if st.session_state.validated:
    r = st.session_state.result

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Energi", f"{r['energi']} kkal")
    c2.metric("Protein", f"{r['protein']} g")
    c3.metric("Karbohidrat", f"{r['karbo']} g")
    c4.metric("Serat", f"{r['serat']} g")

    if r["status"] == "sesuai":
        st.success("✅ Menu memenuhi standar gizi MBG")
    else:
        st.error("❌ Menu tidak memenuhi standar gizi MBG")
