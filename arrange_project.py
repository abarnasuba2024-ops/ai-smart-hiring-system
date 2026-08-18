import os
import shutil

# Main project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Folders that the AI Smart Hiring System needs
folders = [
    "templates",
    "static",
    "static/css",
    "static/js",
    "static/images",
    "uploads",
    "project_files"
]

# Create folders
for folder in folders:
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

# Files that belong inside templates/
template_files = [
    "index.html",
    "add_job.html",
    "candidates.html",
    "candidate_detail.html",
    "upload_resume.html",
    "base.html"
]

# Move HTML files into templates/
for filename in template_files:
    source = os.path.join(BASE_DIR, filename)
    destination = os.path.join(BASE_DIR, "templates", filename)

    if os.path.isfile(source):
        shutil.move(source, destination)
        print(f"Moved: {filename} -> templates/{filename}")


# Python files that should remain in the main project folder
python_files = [
    "app.py",
    "database.py",
    "resume_parser.py",
    "ai_matching.py"
]

for filename in python_files:
    filepath = os.path.join(BASE_DIR, filename)

    if os.path.isfile(filepath):
        print(f"OK: {filename}")


# Create uploads/.gitkeep so the folder is preserved
gitkeep = os.path.join(BASE_DIR, "uploads", ".gitkeep")

if not os.path.exists(gitkeep):
    with open(gitkeep, "w", encoding="utf-8") as file:
        file.write("")


print("\n======================================")
print("PROJECT ARRANGED SUCCESSFULLY")
print("======================================")

print("""
AI_Smart_Hiring_System/
│
├── app.py
├── database.py
├── ai_matching.py
├── resume_parser.py
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── add_job.html
│   ├── candidates.html
│   ├── candidate_detail.html
│   └── upload_resume.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── uploads/
│
├── project_files/
│
└── arrange_project.py
""")

print("You can now run:")
print("python app.py")