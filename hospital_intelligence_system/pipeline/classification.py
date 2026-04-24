def classify_hospital(beds):

    if beds is None:
        return "Unknown"

    if beds < 50:
        return "Small"

    if beds <= 150:
        return "Medium"

    return "Large"