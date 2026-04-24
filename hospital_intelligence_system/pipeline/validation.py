import os
import re
import time
from difflib import SequenceMatcher

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


class HospitalAddressValidationAgent:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("TAVILY_API_KEY is missing in your .env file")

        self.api_key = api_key
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }

    def normalize_text(self, text: str) -> str:
        if text is None or pd.isna(text):
            return ""

        text = str(text).lower().strip()

        replacements = {
            "bengaluru": "bangalore",
            "bangaluru": "bangalore",
            "hubballi": "hubli",
            "rd.": "road",
            " rd ": " road ",
            "st.": "street",
            " st ": " street ",
            "ave.": "avenue",
            " ave ": " avenue ",
            "no.": " ",
            "no ": " ",
            "opp.": " opposite ",
            " opp ": " opposite ",
            "near ": " ",
        }

        padded = f" {text} "
        for old, new in replacements.items():
            padded = padded.replace(old, new)

        text = padded.strip()

        # remove phone numbers
        text = re.sub(r"\b\d{10,13}\b", " ", text)

        # keep commas and slash until late stage
        text = re.sub(r"[^a-z0-9\s,/\-]", " ", text)

        # remove noise phrases
        noise_patterns = [
            r"\bcontact details\b",
            r"\bcontact detail\b",
            r"\blocation\b",
            r"\bcontact number\b",
            r"\bcontact numbers\b",
            r"\bphone number\b",
            r"\bphone numbers\b",
            r"\bmobile number\b",
            r"\bmobile numbers\b",
            r"\bcall us\b",
            r"\bcall\b",
            r"\bget directions\b",
            r"\bdirections\b",
            r"\bwebsite\b",
            r"\bemail\b",
            r"\bindia\b",
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, " ", text)

        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_pincode(self, text: str) -> str:
        match = re.search(r"\b\d{6}\b", text or "")
        return match.group(0) if match else ""

    def tokenize_address(self, text: str) -> set:
        text = self.normalize_text(text)
        stop_words = {
            "hospital", "blood", "bank", "details", "contact", "location",
            "road", "street", "india", "karnataka"
        }
        tokens = set(text.split())
        return {t for t in tokens if len(t) > 2 and t not in stop_words and not t.isdigit()}

    def clean_scraped_candidate(self, text: str) -> str:
        if not text:
            return ""

        text = self.normalize_text(text)

        # remove repeated separators and trim around commas
        text = re.sub(r"\s*,\s*", ", ", text)
        text = re.sub(r"\s+", " ", text).strip(" ,.-")

        return text

    def compare_addresses(self, original: str, web_address: str) -> bool:
        original_clean = self.clean_scraped_candidate(original)
        web_clean = self.clean_scraped_candidate(web_address)

        if not original_clean or not web_clean:
            return False

        if original_clean == web_clean:
            return True

        original_pin = self.extract_pincode(original_clean)
        web_pin = self.extract_pincode(web_clean)
        pin_match = bool(original_pin and web_pin and original_pin == web_pin)

        ratio = SequenceMatcher(None, original_clean, web_clean).ratio()

        original_tokens = self.tokenize_address(original_clean)
        web_tokens = self.tokenize_address(web_clean)

        overlap = 0.0
        if original_tokens and web_tokens:
            overlap = len(original_tokens & web_tokens) / max(len(original_tokens), 1)

        # containment works very well when scraped text is verbose
        if original_clean in web_clean or web_clean in original_clean:
            if pin_match or ratio >= 0.75:
                return True

        # strong direct similarity
        if ratio >= 0.88:
            return True

        # locality + pincode based validation
        if pin_match and overlap >= 0.45:
            return True

        # very strong locality overlap even if one source missed pincode
        if overlap >= 0.75:
            return True

        return False

    def search_web_with_tavily(self, hospital_name: str) -> list:
        query = f"{hospital_name} hospital Karnataka address"

        url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": False,
            "include_raw_content": True,
        }

        print(f"Searching query: {query}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("content", "") or "",
                    "raw_content": item.get("raw_content", "") or "",
                })
            return results

        except Exception as e:
            print(f"Tavily search failed for {hospital_name}: {e}")
            return []

    def fetch_page_text(self, url: str) -> str:
        if not url:
            return ""

        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            return soup.get_text("\n", strip=True)
        except Exception:
            return ""

    def extract_address_candidates(self, text: str) -> list:
        if not text:
            return []

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        candidates = []

        keywords = [
            "road", "street", "layout", "nagar", "main", "cross", "phase",
            "bangalore", "bengaluru", "hubli", "hubballi", "mysore", "mysuru",
            "karnataka", "india", "pin", "pincode", "district", "opp",
            "opposite", "location", "address"
        ]

        for line in lines:
            low = line.lower()

            has_keyword = any(k in low for k in keywords)
            has_pincode = bool(re.search(r"\b\d{6}\b", line))

            if len(line) >= 15 and len(line) <= 350 and (has_keyword or has_pincode):
                candidates.append(line)

        # Also try sentence split for inline snippets
        sentence_parts = re.split(r"[|•;\n]", text)
        for part in sentence_parts:
            part = part.strip()
            low = part.lower()
            has_keyword = any(k in low for k in keywords)
            has_pincode = bool(re.search(r"\b\d{6}\b", part))
            if len(part) >= 15 and len(part) <= 350 and (has_keyword or has_pincode):
                candidates.append(part)

        unique = []
        seen = set()
        for c in candidates:
            cleaned = self.clean_scraped_candidate(c)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique.append(cleaned)

        return unique

    def score_candidate_against_original(self, original_address: str, candidate: str) -> float:
        orig = self.clean_scraped_candidate(original_address)
        cand = self.clean_scraped_candidate(candidate)

        if not cand:
            return 0.0

        ratio = SequenceMatcher(None, orig, cand).ratio()

        orig_tokens = self.tokenize_address(orig)
        cand_tokens = self.tokenize_address(cand)

        overlap = 0.0
        if orig_tokens and cand_tokens:
            overlap = len(orig_tokens & cand_tokens) / max(len(orig_tokens), 1)

        orig_pin = self.extract_pincode(orig)
        cand_pin = self.extract_pincode(cand)
        pin_bonus = 0.20 if (orig_pin and cand_pin and orig_pin == cand_pin) else 0.0

        contains_bonus = 0.15 if (orig in cand or cand in orig) else 0.0

        return ratio + (0.6 * overlap) + pin_bonus + contains_bonus

    def pick_best_address(self, original_address: str, results: list) -> str:
        best_address = ""
        best_score = -1.0
        fallback_address = ""

        for result in results:
            text_blocks = [
                result.get("description", ""),
                result.get("raw_content", ""),
                self.fetch_page_text(result.get("url", "")),
            ]

            for block in text_blocks:
                candidates = self.extract_address_candidates(block)

                for candidate in candidates:
                    cleaned_candidate = self.clean_scraped_candidate(candidate)

                    if not fallback_address and cleaned_candidate:
                        fallback_address = cleaned_candidate

                    score = self.score_candidate_against_original(original_address, cleaned_candidate)

                    if score > best_score:
                        best_score = score
                        best_address = cleaned_candidate

        # if nothing scored but something was seen, still return fallback
        if not best_address and fallback_address:
            return fallback_address

        return best_address

    def validate_hospital(self, hospital_name: str, original_address: str):
        results = self.search_web_with_tavily(hospital_name)
        if not results:
            return False, ""

        web_address = self.pick_best_address(original_address, results)
        is_valid = self.compare_addresses(original_address, web_address)

        print(f"Hospital: {hospital_name}")
        print(f"Original Address: {original_address}")
        print(f"Web Address: {web_address}")
        print(f"Verified: {is_valid}")
        print("=" * 100)

        return is_valid, web_address


def run_validation(input_file: str, output_file: str, limit: int = 10):
    df = pd.read_excel(input_file)
    agent = HospitalAddressValidationAgent(TAVILY_API_KEY)

    output_rows = []

    for index, row in df.head(limit).iterrows():
        hospital_name = row.get("Hospitals Name", "")
        original_address = row.get("Hospital Address", "")

        try:
            address_verified, hospital_verified_address = agent.validate_hospital(
                hospital_name,
                original_address,
            )

            new_row = row.to_dict()
            new_row["Address_Verified"] = address_verified
            new_row["Hospital_Verified_Address"] = hospital_verified_address
            output_rows.append(new_row)

        except Exception as e:
            print(f"Error in row {index + 1} for {hospital_name}: {e}")
            new_row = row.to_dict()
            new_row["Address_Verified"] = False
            new_row["Hospital_Verified_Address"] = ""
            output_rows.append(new_row)

        time.sleep(2)

    pd.DataFrame(output_rows).to_excel(output_file, index=False)
    print(f"Saved output to: {output_file}")


if __name__ == "__main__":
    input_file = "/Users/manyaachanta/Documents/N2WORK/hospital_intelligence_system/data/raw/Karnataka-All-data.xlsx"
    output_file = "/Users/manyaachanta/Documents/N2WORK/hospital_intelligence_system/data/processed/validated_addresses.xlsx"
    run_validation(input_file, output_file, limit=10)