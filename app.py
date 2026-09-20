from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)

# ==================================================
# PROJECT PATHS
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If app.py is inside templates folder,
# HTML files are in the same folder.
if os.path.basename(BASE_DIR).lower() == "templates":
    TEMPLATE_FOLDER = BASE_DIR
else:
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ==================================================
# JOB SKILLS
# ==================================================

JOB_SKILLS = {

    "Python Developer": [
        "python",
        "flask",
        "django",
        "sql",
        "git"
    ],

    "Data Scientist": [
        "python",
        "machine learning",
        "pandas",
        "numpy",
        "sql"
    ],

    "Web Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "bootstrap"
    ],

    "Java Developer": [
        "java",
        "spring",
        "sql",
        "hibernate",
        "git"
    ],

    "Full Stack Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node",
        "sql"
    ],

    "Machine Learning Engineer": [
        "python",
        "machine learning",
        "tensorflow",
        "pytorch",
        "numpy"
    ]
}


# ==================================================
# FILE CHECK
# ==================================================

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in [
        "pdf",
        "docx"
    ]


# ==================================================
# PDF TEXT
# ==================================================

def extract_pdf_text(filepath):

    try:

        from PyPDF2 import PdfReader

    except ImportError:

        return (
            "PyPDF2 is not installed. "
            "Run: pip install PyPDF2"
        )

    text = ""

    try:

        reader = PdfReader(filepath)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as error:

        print("PDF ERROR:", error)

    return text


# ==================================================
# DOCX TEXT
# ==================================================

def extract_docx_text(filepath):

    try:

        from docx import Document

    except ImportError:

        return (
            "python-docx is not installed. "
            "Run: pip install python-docx"
        )

    text = ""

    try:

        document = Document(filepath)

        for paragraph in document.paragraphs:

            if paragraph.text:
                text += paragraph.text + "\n"

    except Exception as error:

        print("DOCX ERROR:", error)

    return text


# ==================================================
# RESUME TEXT
# ==================================================

def extract_resume_text(filepath):

    extension = filepath.rsplit(
        ".",
        1
    )[1].lower()

    if extension == "pdf":

        return extract_pdf_text(filepath)

    if extension == "docx":

        return extract_docx_text(filepath)

    return ""


# ==================================================
# SKILL DETECTION
# ==================================================

def detect_skills(text, required_skills):

    text = text.lower()

    found = []

    for skill in required_skills:

        skill_lower = skill.lower()

        if re.search(
            r"\b"
            + re.escape(skill_lower)
            + r"\b",
            text
        ):

            found.append(skill)

    return found


# ==================================================
# SCORE
# ==================================================

def calculate_score(
    found_skills,
    required_skills
):

    if not required_skills:

        return 0

    score = (
        len(found_skills)
        / len(required_skills)
    ) * 100

    return round(score)


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# ==================================================
# CANDIDATE
# ==================================================

@app.route(
    "/candidate",
    methods=["GET", "POST"]
)
def candidate():

    # --------------------------
    # OPEN CANDIDATE PAGE
    # --------------------------

    if request.method == "GET":

        return render_template(
            "candidate.html",
            job_roles=list(
                JOB_SKILLS.keys()
            )
        )

    # --------------------------
    # FORM DATA
    # --------------------------

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

    # --------------------------
    # VALIDATION
    # --------------------------

    if not name:

        return "Please enter candidate name."

    if not email:

        return "Please enter candidate email."

    if not job_role:

        return "Please select a job role."

    if resume is None:

        return "Please upload a resume."

    if resume.filename == "":

        return "Please select a resume file."

    if not allowed_file(
        resume.filename
    ):

        return (
            "Invalid file. "
            "Please upload PDF or DOCX."
        )

    # --------------------------
    # SAVE FILE
    # --------------------------

    filename = secure_filename(
        resume.filename
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    resume.save(filepath)

    # --------------------------
    # READ RESUME
    # --------------------------

    resume_text = extract_resume_text(
        filepath
    )

    # --------------------------
    # REQUIRED SKILLS
    # --------------------------

    required_skills = JOB_SKILLS.get(
        job_role,
        []
    )

    # --------------------------
    # FIND SKILLS
    # --------------------------

    found_skills = detect_skills(
        resume_text,
        required_skills
    )

    # --------------------------
    # SCORE
    # --------------------------

    score = calculate_score(
        found_skills,
        required_skills
    )

    # --------------------------
    # DECISION
    # --------------------------

    if score >= 60:

        decision = "SELECT"

    else:

        decision = "REJECT"

    # --------------------------
    # RESULT PAGE
    # --------------------------

    return render_template(
        "resume_result.html",

        name=name,

        email=email,

        mobile=mobile,

        location=location,

        job_role=job_role,

        filename=filename,

        required_skills=required_skills,

        found_skills=found_skills,

        score=score,

        decision=decision
    )


# ==================================================
# ADD JOB
# ==================================================

@app.route(
    "/add-job",
    methods=["GET", "POST"]
)
def add_job():

    # --------------------------
    # OPEN JOB PAGE
    # --------------------------

    if request.method == "GET":

        return render_template(
            "add_job.html"
        )

    # --------------------------
    # GET FORM DATA
    # --------------------------

    job_title = request.form.get(
        "job_title",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    employment_type = request.form.get(
        "employment_type",
        ""
    ).strip()

    experience = request.form.get(
        "experience",
        ""
    ).strip()

    skills = request.form.get(
        "skills",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    # --------------------------
    # SIMPLE VALIDATION
    # --------------------------

    if not job_title:

        return "Please enter job title."

    if not location:

        return "Please enter location."

    # --------------------------
    # PRINT JOB
    # --------------------------

    print("")
    print("==========================")
    print("NEW JOB CREATED")
    print("==========================")
    print("Job Title:", job_title)
    print("Location:", location)
    print("Employment:", employment_type)
    print("Experience:", experience)
    print("Skills:", skills)
    print("Description:", description)
    print("==========================")
    print("")

    return redirect(
        url_for("dashboard")
    )


# ==================================================
# ERROR HANDLERS
# ==================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>Please check the URL.</p>
    """, 404


@app.errorhandler(500)
def server_error(error):

    print("SERVER ERROR:", error)

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Please check the VS Code terminal.</p>
    """, 500


# ==================================================
# START APP
# ==================================================

if __name__ == "__main__":

    print("")
    print("======================================")
    print("       AI SMART HIRING SYSTEM")
    print("======================================")
    print("APP LOCATION:")
    print(BASE_DIR)
    print("")
    print("TEMPLATE LOCATION:")
    print(TEMPLATE_FOLDER)
    print("")
    print("UPLOAD LOCATION:")
    print(UPLOAD_FOLDER)
    print("")
    print("======================================")
    print("OPEN:")
    print("http://127.0.0.1:5000")
    print("======================================")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )