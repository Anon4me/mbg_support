import pandas as pd


def group_age(age: int, age_df: pd.DataFrame):
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


def group_up(level: str, grade: int, edu_df: pd.DataFrame, gender: str = "all"):
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


def get_standard(group_id: str, std_df: pd.DataFrame):
    row = std_df[std_df["group_id"] == group_id]

    if row.empty:
        raise ValueError("Standar MBG tidak ditemukan")

    return row.iloc[0]


def evaluasi_mbg(total: dict, std: pd.Series):
    return {
        "energy_status": (
            "LOW"
            if total["energy"] < std["min_energy_kcal"]
            else "HIGH"
            if total["energy"] > std["max_energy_kcal"]
            else "OK"
        ),
        "protein_ok": total["protein"] >= std["min_protein_g"],
        "animal_protein_ok": total["animal_protein"] >= std["min_animal_protein_g"],
        "fiber_ok": total["fiber"] >= std["min_fiber_g"],
    }


if __name__ == "__main__":
    age_df = pd.read_csv("data/age_group.csv")
    edu_df = pd.read_csv("data/education_level.csv")
    std_df = pd.read_csv("data/standar_mbg.csv")

    age = 10
    total_nutrition = {
        "energy": 1650,
        "protein": 42,
        "animal_protein": 20,
        "fiber": 18,
    }

    level, grade, gender = group_age(age, age_df)
    group_id = group_up(level, grade, edu_df, gender)
    standard = get_standard(group_id, std_df)
    result = evaluasi_mbg(total_nutrition, standard)

    print(level, grade, gender, group_id, result)
