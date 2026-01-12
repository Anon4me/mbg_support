# =========================
# IMPORT & SETUP
# =========================
import streamlit as st
import pandas as pd
import time
import uuid

st.set_page_config(
    page_title="AI Validasi Menu MBG",
    layout="wide"
)

# =========================
# STATE INIT
# =========================
if "student_info" not in st.session_state:
    st.session_state.student_info = {
        "jenjang": "",
        "kelas": "",
        "gender": ""
    }

if "menu_items" not in st.session_state:
    st.session_state.menu_items = []

if "validated" not in st.session_state:
    st.session_state.validated = False

if "result" not in st.session_state:
    st.session_state.result = None

if "logbook" not in st.session_state:
    st.session_state.logbook = []

# =========================
# DATA MASTER
# =========================
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

# =========================
# HEADER
# =========================
st.title("🍽️ AI Validasi Menu MBG")
st.caption("Validasi otomatis menu sesuai standar gizi MBG")

# =========================
# INFORMASI SISWA
# =========================
st.subheader("👤 Informasi Siswa")

info = st.session_state.student_info

col1, col2, col3 = st.columns(3)

with col1:
    jenjang = st.selectbox(
        "Jenjang Pendidikan",
        ["", "SD", "SMP", "SMA"],
        index=["", "SD", "SMP", "SMA"].index(info["jenjang"]) if info["jenjang"] in ["SD", "SMP", "SMA"] else 0
    )

if jenjang != info["jenjang"]:
    info["jenjang"] = jenjang
    info["kelas"] = ""
    info["gender"] = "Semua" if jenjang == "SD" else ""

with col2:
    kelas = st.selectbox(
        "Kelas",
        ["Pilih Jenjang Terlebih Dahulu"] if not info["jenjang"] else [""] + KELAS_OPTIONS[info["jenjang"]],
        disabled=not info["jenjang"]
    )

    if kelas and kelas != "Pilih Jenjang Terlebih Dahulu":
        info["kelas"] = kelas

with col3:
    if info["jenjang"] == "SD":
        gender = st.selectbox(
            "Jenis Kelamin",
            ["Semua"],
            disabled=True
        )
        info["gender"] = "Semua"
    else:
        gender = st.selectbox(
            "Jenis Kelamin",
            ["", "Perempuan", "Laki-laki", "Semua"]
        )
        info["gender"] = gender

# =========================
# MENU SELECTION
# =========================
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

# =========================
# PORTION CONTROL
# =========================
st.subheader("⚖️ Kontrol Porsi")

if not st.session_state.menu_items:
    st.info("Pilih menu terlebih dahulu")
else:
    for item in st.session_state.menu_items:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{item['name']}**")
        item["custom"] = c2.checkbox("Porsi Bebas", item["custom"], key=f"c_{item['id']}")
        item["portion"] = c3.number_input(
            "gram",
            min_value=0,
            step=10,
            value=item["portion"],
            disabled=not item["custom"],
            key=f"p_{item['id']}"
        )

# =========================
# AI VALIDATION
# =========================
st.subheader("✨ AI Validasi Menu")

can_validate = (
    info["jenjang"] and
    info["kelas"] and
    info["gender"] and
    len(st.session_state.menu_items) > 0
)

if st.button("Validasi Menu", disabled=not can_validate):
    with st.spinner("Memproses menu dengan AI..."):
        time.sleep(1)
        st.info("Menganalisis komposisi nutrisi...")
        time.sleep(1)
        st.info("Memeriksa kepatuhan SOP...")
        time.sleep(1)
        st.info("Menyusun laporan...")
        time.sleep(1)

    energi = sum(i["portion"] * 1.2 for i in st.session_state.menu_items)
    protein = sum(i["portion"] * 0.08 for i in st.session_state.menu_items)
    karbo = sum(i["portion"] * 0.2 for i in st.session_state.menu_items)
    serat = sum(i["portion"] * 0.03 for i in st.session_state.menu_items)

    status = "sesuai" if energi >= 400 else "tidak sesuai"

    st.session_state.result = {
        "energi": int(energi),
        "protein": int(protein),
        "karbohidrat": int(karbo),
        "serat": int(serat),
        "status": status,
        "message": "Menu memenuhi standar MBG" if status == "sesuai" else "Energi belum mencukupi"
    }

    if status == "sesuai":
        st.session_state.logbook.append({
            "id": str(uuid.uuid4()),
            "namaMenu": ", ".join(i["name"] for i in st.session_state.menu_items),
            "bahanUtama": st.session_state.menu_items[0]["name"],
            "kelas": info["kelas"],
            "energi": int(energi),
            "statusSOP": "Sesuai SOP"
        })

    st.session_state.validated = True

# =========================
# NUTRITION OUTPUT
# =========================
if st.session_state.validated:
    st.subheader("📊 Output Laporan Gizi")

    r = st.session_state.result
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Energi", f"{r['energi']} kkal")
    c2.metric("Protein", f"{r['protein']} g")
    c3.metric("Karbohidrat", f"{r['karbohidrat']} g")
    c4.metric("Serat", f"{r['serat']} g")

    st.success(f"✅ {r['message']}") if r["status"] == "sesuai" else st.error(f"❌ {r['message']}")

