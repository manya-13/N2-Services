from pipeline.ingestion import load_hospital_data
from pipeline.cleaning import clean_phone_numbers, clean_email

def run_pipeline():

    df = load_hospital_data("data/raw/Karnataka-All-data.xlsx")

    df["clean_phone"] = df["Number"].apply(clean_phone_numbers)
    df["clean_email"] = df["Email"].apply(clean_email)

    df.to_csv("data/processed/clean_hospitals.csv", index=False)

if __name__ == "__main__":
    run_pipeline()