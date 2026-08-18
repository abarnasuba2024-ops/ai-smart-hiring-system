from PyPDF2 import PdfReader
import re


def extract_text_from_pdf(file_path):
    text = ""

    try:
        reader = PdfReader(file_path)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        print("PDF extraction error:", e)

    return text


def extract_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return ""


def extract_phone(text):
    pattern = r"(\+?\d[\d\s\-]{8,15}\d)"

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return ""


def extract_name(text):
    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if "@" in line:
            continue

        if any(char.isdigit() for char in line):
            continue

        if 2 <= len(line.split()) <= 5:
            return line

    return "Unknown Candidate"