from rapidfuzz import fuzz

def is_duplicate(name1, name2):
    score = fuzz.ratio(name1.lower(), name2.lower())
    return score > 90