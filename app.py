from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import re

# PDF
from PyPDF2 import PdfReader

# DOCX
from docx import Document


app = Flask(__name__)

app.secret_key = "ai-smart-hiring-secret-key"

# --------------------------------------------------
# Configuration
# --------------------------------------------------

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# Job Role Skills
# --------------------------------------------------

JOB_SKILLS = {

    "Python Developer": [
        "python",
        "flask",
        "django",
        "rest api",
        "sql",
        "postgresql",
        "mysql",
        "git",
        "github",
        "html",
        "css",
        "javascript",
        "api",
        "docker"
    ],

    "Java Developer": [
        "java",
        "spring",
        "spring boot",
        "hibernate",
        "sql",
        "mysql",
        "rest api",
        "git"
    ],

    "Web Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "php",
        "sql",
        "git"
    ],

    "Full Stack Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "python",
        "java",
        "sql",
        "mongodb",
        "git",
        "rest api"
    ],

    "Data Analyst": [
        "python",
        "sql",
        "excel",
        "power bi",
        "tableau",
        "pandas",
        "numpy",
        "data analysis"
    ],

    "Data Scientist": [
        "python",
        "machine learning",
        "deep learning",
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "sql",
        "statistics"
    ],

    "Software Engineer": [
        "python",
        "java",
        "c++",
        "sql",
        "git",
        "data structures",
        "algorithms",
        "rest api"
    ]
}


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def extract_pdf_text(filepath):

    text = ""

    try:

        reader = PdfReader(filepath)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:

        print("PDF extraction error:", e)

    return text


def extract_docx_text(filepath):

    text = ""

    try:

        document = Document(filepath)

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

    except Exception as e:

        print("DOCX extraction error:", e)

    return text


def extract_resume_text(filepath):

    extension = filepath.rsplit(".", 1)[1].lower()

    if extension == "pdf":

        return extract_pdf_text(filepath)

    elif extension == "docx":

        return extract_docx_text(filepath)

    return ""


def normalize_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-zA-Z0-9+#.\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def find_skills(resume_text, required_skills):

    normalized_resume = normalize_text(resume_text)

    found_skills = []

    for skill in required_skills:

        skill_lower = skill.lower()

        if skill_lower in normalized_resume:

            found_skills.append(skill)

    return found_skills


def calculate_score(found_skills, required_skills):

    if not required_skills:

        return 0

    score = (
        len(found_skills)
        / len(required_skills)
    ) * 100

    return round(score)


def generate_summary(
    candidate_name,
    job_role,
    found_skills,
    score
):

    if score >= 80:

        recommendation = (
            "Strong match for the selected job role."
        )

    elif score >= 60:

        recommendation = (
            "Moderate match. Further review is recommended."
        )

    else:

        recommendation = (
            "Low match for the selected job role."
        )

    skill_text = ", ".join(found_skills)

    return (
        f"{candidate_name} applied for the "
        f"{job_role} position. "
        f"Detected skills: {skill_text}. "
        f"{recommendation}"
    )


# --------------------------------------------------
# Home
# --------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# --------------------------------------------------
# Candidate Application
# --------------------------------------------------

@app.route(
    "/candidate",
    methods=["GET", "POST"]
)
def candidate():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        job_role = request.form.get(
            "job_role",
            ""
        ).strip()

        resume = request.files.get(
            "resume"
        )


        # ------------------------------------------
        # Validation
        # ------------------------------------------

        if not name:

            flash("Please enter candidate name.")

            return redirect(
                url_for("candidate")
            )


        if not email:

            flash("Please enter email.")

            return redirect(
                url_for("candidate")
            )


        if not mobile:

            flash("Please enter mobile number.")

            return redirect(
                url_for("candidate")
            )


        if not location:

            flash("Please enter location.")

            return redirect(
                url_for("candidate")
            )


        if not job_role:

            flash("Please select a job role.")

            return redirect(
                url_for("candidate")
            )


        if not resume:

            flash("Please upload a resume.")

            return redirect(
                url_for("candidate")
            )


        if resume.filename == "":

            flash("Please select a resume file.")

            return redirect(
                url_for("candidate")
            )


        if not allowed_file(resume.filename):

            flash(
                "Only PDF and DOCX resumes are supported."
            )

            return redirect(
                url_for("candidate")
            )


        # ------------------------------------------
        # Save Resume
        # ------------------------------------------

        filename = secure_filename(
            resume.filename
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        resume.save(filepath)


        # ------------------------------------------
        # Extract Resume Text
        # ------------------------------------------

        resume_text = extract_resume_text(
            filepath
        )


        if not resume_text.strip():

            flash(
                "Could not read the resume. "
                "Please upload a text-based PDF or DOCX."
            )

            return redirect(
                url_for("candidate")
            )


        # ------------------------------------------
        # Get Required Skills
        # ------------------------------------------

        required_skills = JOB_SKILLS.get(
            job_role,
            []
        )


        # ------------------------------------------
        # Find Skills
        # ------------------------------------------

        found_skills = find_skills(
            resume_text,
            required_skills
        )


        # ------------------------------------------
        # Calculate Score
        # ------------------------------------------

        score = calculate_score(
            found_skills,
            required_skills
        )


        # ------------------------------------------
        # Generate Summary
        # ------------------------------------------

        summary = generate_summary(
            name,
            job_role,
            found_skills,
            score
        )


        # ------------------------------------------
        # Decision
        # ------------------------------------------

        if score >= 70:

            recommendation = "SELECT"

        else:

            recommendation = "REJECT"


        # ------------------------------------------
        # Show Result
        # ------------------------------------------

        return render_template(
            "resume_result.html",

            name=name,

            email=email,

            mobile=mobile,

            location=location,

            job_role=job_role,

            resume_filename=filename,

            resume_summary=summary,

            found_skills=found_skills,

            required_skills=required_skills,

            score=score,

            recommendation=recommendation
        )


    return render_template(
        "candidate.html"
    )


# --------------------------------------------------
# Select Candidate
# --------------------------------------------------

@app.route(
    "/select/<candidate_name>"
)
def select_candidate(candidate_name):

    return (
        f"Candidate {candidate_name} "
        f"has been selected successfully."
    )


# --------------------------------------------------
# Reject Candidate
# --------------------------------------------------

@app.route(
    "/reject/<candidate_name>"
)
def reject_candidate(candidate_name):

    return (
        f"Candidate {candidate_name} "
        f"has been rejected."
    )


# --------------------------------------------------
# Error: File Too Large
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):

    return (
        "Resume file is too large. "
        "Maximum size is 10 MB.",
        413
    )


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
