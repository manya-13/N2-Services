import requests
from bs4 import BeautifulSoup

def scrape_hospital_info(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text().lower()

        if "cardiology" in text:
            return "Cardiology"

        if "nephrology" in text:
            return "Nephrology"

        return "General"

    except:
        return None