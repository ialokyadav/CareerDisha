from typing import Dict, List
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from common.utils import normalize_text


def extract_keywords(cleaned_text: str, top_k: int = 15) -> List[str]:
    if not cleaned_text:
        return []
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=200)
    X = vectorizer.fit_transform([cleaned_text])
    scores = X.toarray()[0]
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    return [term for term, _ in ranked[:top_k]]


def extract_education(text: str) -> Dict[str, str]:
    """
    Extracts college names and higher education levels using regex.
    """
    # Common degree patterns
    degree_patterns = [
        r"\b(B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|B\.?A|M\.?A|MBA|PHD|Bachelor|Master|Post\s*Graduate)\b",
    ]
    
    # Common college/university keywords
    college_keywords = ["University", "Institute", "College", "Academy", "School of", "IIT", "NIT", "BITS"]

    education = {
        "higher_education": "Not found",
        "college": "Not found"
    }

    # Find degree
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            education["higher_education"] = match.group(0)
            break

    # Find college (usually follows or precedes degree, or contains keywords)
    # Simple strategy: look for sentences containing college keywords
    lines = text.split('\n')
    for line in lines:
        if any(kw.lower() in line.lower() for kw in college_keywords):
            # Clean up the line a bit
            education["college"] = line.strip()
            break
            
    return education


def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Extracts email and phone number using regex.
    """
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    # Supports international formats with optional country code, separators, and parentheses.
    phone_pattern = r"(?:\+|00)?\d{1,3}[\s\-\.]?(?:\(?\d{2,5}\)?[\s\-\.]?){1,4}\d{2,6}"
    
    email_match = re.search(email_pattern, text)
    phone_match = re.search(phone_pattern, text)

    phone = "Not found"
    if phone_match:
        candidate = phone_match.group(0).strip()
        # Keep original formatting but ensure it has enough digits to be a real phone number.
        digit_count = len(re.sub(r"\D", "", candidate))
        if digit_count >= 8:
            phone = candidate
    
    return {
        "email": email_match.group(0) if email_match else "Not found",
        "phone": phone
    }


def parse_resume_text(raw_text: str) -> Dict[str, any]:
    cleaned = normalize_text(raw_text)
    keywords = extract_keywords(cleaned)
    education = extract_education(raw_text)
    contact = extract_contact_info(raw_text)
    
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned,
        "keywords": keywords,
        "education": education,
        "contact": contact
    }
