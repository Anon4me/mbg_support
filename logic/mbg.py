import pandas as pd

age_df = pd.read_csv("data/age_group.csv")
edu_df = pd.read_csv("data/education_level.csv")
std_df = pd.read_csv("data/standar_mbg.csv")


def resolve_age(age, age_df):
    row = age_df[
        (age_df["age_min"] <= age) &
        (age_df["age_max"] >= age)
    ]

    if row.empty:
        raise ValueError("Usia tidak valid")

    return (
        row.iloc[0]["education_level"],
        int(row.iloc[0]["grade"]),
        row.iloc[0]["default_gender"]
    )


def resolve_group(level, grade, edu_df, gender="all"):
    df = edu_df[
        (edu_df["level"] == level) &
        (edu_df["class_min"] <= grade) &
        (edu_df["class_max"] >= grade)
    ]

    if gender != "all":
        suffix = "_M" if gender.lower() == "male" else "_F"
        df = df[df["group_id"].str.endswith(suffix)]

    if df.empty:
        raise ValueError("Group MBG tidak ditemukan")

    return df.iloc[0]["group_id"]


def get_standard(group_id, std_df):
    row = std_df[std_df["group_id"] == group_id]

    if row.empty:
        raise ValueError("Standar MBG tidak ditemukan")

    return row.iloc[0]


def evaluate(total, std):
    return {
        "energy_status": (
            "LOW" if total["energy"] < std["min_energy_kcal"]
            else "HIGH" if total["energy"] > std["max_energy_kcal"]
            else "OK"
        ),
        "protein_ok": total["protein"] >= std["min_protein_g"],
        "animal_protein_ok": total["animal_protein"] >= std["min_animal_protein_g"],
        "fiber_ok": total["fiber"] >= std["min_fiber_g"]
    }


if __name__ == "__main__":
    age = 10
    total_nutrition = {
        "energy": 1650,
        "protein": 42,
        "animal_protein": 20,
        "fiber": 18
    }

    level, grade, gender = resolve_age(age, age_df)
    group_id = resolve_group(level, grade, edu_df, gender)
    standard = get_standard(group_id, std_df)
    result = evaluate(total_nutrition, standard)

    print("Education Level:", level)
    print("Grade:", grade)
    print("Gender:", gender)
    print("Group ID:", group_id)
    print("Evaluation Result:", result)
