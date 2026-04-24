from email_validator import validate_email, EmailNotValidError
import requests
from bs4 import BeautifulSoup
import re

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_email_via_website(website, email):
    """
    Validates if the given email is found on the hospital's website.
    This acts as an AI agent that checks the website for contact emails.
    """
    if not website or not email:
        return False
    
    try:
        # Ensure website has http/https
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        response = requests.get(website, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # Extract emails using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, text, re.IGNORECASE)
        
        # Check if the given email is in the found emails (case insensitive)
        return email.lower() in [e.lower() for e in found_emails]
    
    except Exception as e:
        print(f"Error validating email via website {website}: {e}")
        return False