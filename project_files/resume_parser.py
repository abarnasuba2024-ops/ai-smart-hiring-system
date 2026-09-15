from PyPDF2 import PdfReader
import re


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

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

    return format_resume_text(text)


# =========================================================
# RESUME TEXT FORMATTER
# =========================================================

def format_resume_text(text):
    """
    Converts extracted resume text into readable sections
    and bullet points.
    """

    if not text:
        return ""

    # -----------------------------------------
    # Basic cleanup
    # -----------------------------------------

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize bullet characters
    text = text.replace("●", "•")
    text = text.replace("▪", "•")
    text = text.replace("◦", "•")
    text = text.replace("·", "•")

    # -----------------------------------------
    # Put bullets on separate lines
    # -----------------------------------------

    text = re.sub(r"\s*•\s*", "\n• ", text)

    # -----------------------------------------
    # Known resume section headings
    # -----------------------------------------

    section_names = [
        "SUMMARY",
        "PROFILE",
        "OBJECTIVE",
        "CAREER OBJECTIVE",
        "PROFESSIONAL SUMMARY",
        "TECHNICAL SKILLS",
        "TECHNICAL SKILL",
        "SKILLS",
        "KEY SKILLS",
        "PROGRAMMING SKILLS",
        "SOFT SKILLS",
        "PROJECTS",
        "PROJECT",
        "WORK EXPERIENCE",
        "EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "INTERNSHIP",
        "INTERNSHIPS",
        "EDUCATION",
        "EDUCATIONAL QUALIFICATION",
        "QUALIFICATIONS",
        "CERTIFICATIONS",
        "CERTIFICATION",
        "ACHIEVEMENTS",
        "AWARDS",
        "LANGUAGES",
        "INTERESTS",
        "HOBBIES",
        "CONTACT",
        "CONTACT INFORMATION",
    ]

    # -----------------------------------------
    # Add line breaks before section headings
    # -----------------------------------------

    for section in section_names:

        pattern = r"\s+" + re.escape(section) + r"\s*"

        replacement = "\n\n" + section.title() + "\n"

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )

    # -----------------------------------------
    # Handle headings at beginning
    # -----------------------------------------

    for section in section_names:

        pattern = r"^" + re.escape(section) + r"\s*"

        replacement = section.title() + "\n"

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )

    # -----------------------------------------
    # Common labels
    # -----------------------------------------

    labels = [
        "Name:",
        "Email:",
        "Phone:",
        "Mobile:",
        "LinkedIn:",
        "GitHub:",
        "Address:"
    ]

    for label in labels:

        text = re.sub(
            r"\s*" + re.escape(label),
            "\n" + label,
            text,
            flags=re.IGNORECASE
        )

    # -----------------------------------------
    # Separate contact information
    # -----------------------------------------

    text = re.sub(
        r"\s*\|\s*",
        "\n",
        text
    )

    # -----------------------------------------
    # Put URLs on separate lines
    # -----------------------------------------

    text = re.sub(
        r"\s+(https?://)",
        r"\n\1",
        text
    )

    # -----------------------------------------
    # Separate common project separators
    # -----------------------------------------

    text = re.sub(
        r"\s+(Face Recognition|Daily Quotes|Student Result)",
        r"\n• \1",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------------
    # Clean lines
    # -----------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove excessive spaces
        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    # -----------------------------------------
    # Detect long lines and create bullets
    # -----------------------------------------

    formatted_lines = []

    current_section = False

    for line in lines:

        # Section heading
        if line.title() in [
            s.title() for s in section_names
        ]:

            formatted_lines.append("")
            formatted_lines.append(line)
            formatted_lines.append("")

            current_section = True

            continue

        # Already a bullet
        if line.startswith("•"):

            formatted_lines.append(line)

            continue

        # Contact information
        if (
            "@" in line
            or line.lower().startswith("phone:")
            or line.lower().startswith("mobile:")
            or line.lower().startswith("linkedin:")
            or line.lower().startswith("github:")
        ):

            formatted_lines.append("• " + line)

            continue

        # Long lines inside resume
        if current_section and len(line) > 80:

            # Keep summary as paragraph
            formatted_lines.append(line)

        else:

            formatted_lines.append(line)

    # -----------------------------------------
    # Remove duplicate blank lines
    # -----------------------------------------

    result = "\n".join(formatted_lines)

    result = re.sub(
        r"\n{3,}",
        "\n\n",
        result
    )

    return result.strip()


# =========================================================
# EMAIL EXTRACTION
# =========================================================

def extract_email(text):

    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return ""


# =========================================================
# PHONE EXTRACTION
# =========================================================

def extract_phone(text):

    pattern = r"(\+?\d[\d\s\-]{8,15}\d)"

    match = re.search(pattern, text)

    if match:

        phone = match.group(0).strip()

        return phone

    return ""


# =========================================================
# NAME EXTRACTION
# =========================================================

def extract_name(text):

    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        # Remove bullet
        line = re.sub(r"^•\s*", "", line)

        if not line:
            continue

        if "@" in line:
            continue

        if "http" in line.lower():
            continue

        if any(char.isdigit() for char in line):
            continue

        # Skip common headings
        if line.upper() in [
            "SUMMARY",
            "PROFILE",
            "OBJECTIVE",
            "TECHNICAL SKILLS",
            "SKILLS",
            "PROJECTS",
            "EDUCATION",
            "EXPERIENCE",
            "CERTIFICATIONS",
            "LANGUAGES"
        ]:
            continue

        # Name usually contains 2-5 words
        if 2 <= len(line.split()) <= 5:

            return line

    return "Unknown Candidate"