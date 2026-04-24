import re

def clean_phone_numbers(text):
    if not isinstance(text, str):
        return None
    
    numbers = re.findall(r'\d{10}', text)
    return numbers[0] if numbers else None
def clean_email(email):
    if isinstance(email, str):
        return email.strip().lower()
    return None