# 🤖 AI Smart Hiring System

An AI-powered recruitment management web application built using **Python Flask** and **SQLite**.  
The system helps recruiters manage jobs, upload candidate resumes, analyze resume content, and match candidates with suitable job positions.

---

## 🚀 Features

- 🔐 Recruiter Login
- 📊 Recruitment Dashboard
- 💼 Add and Manage Job Positions
- 👤 Add and Manage Candidates
- 📄 Resume Upload
- 📝 Resume Text Extraction
- 🤖 Automated Resume Analysis
- 🎯 Job-Candidate Matching
- 📈 Candidate Scoring
- 📌 Candidate Status Management
- 👁️ Candidate Details View
- 🗑️ Delete Candidates
- 🗑️ Delete Jobs
- 📱 Responsive User Interface
- 📅 Dynamic Date and Time
- 👋 Dynamic Dashboard Greeting

---

## 🛠️ Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask

### Database
- SQLite

### Resume Processing
- PyPDF2 / PDF extraction
- python-docx
- OCR support
- Resume text processing

---

## 📂 Project Structure

```text
AI-Smart-Hiring/
│
├── app.py
├── resume_parser.py
├── requirements.txt
├── README.md
│
├── database/
│   └── hiring.db
│
├── uploads/
│   └── candidate resumes
│
├── static/
│   └── style.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── dashboard.html
    ├── add_job.html
    ├── job_detail.html
    ├── candidates.html
    ├── candidate_detail.html
    └── upload_resume.html
