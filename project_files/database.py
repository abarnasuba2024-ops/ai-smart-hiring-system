import sqlite3

DATABASE = "hiring.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            experience INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            resume_filename TEXT,
            resume_text TEXT,
            match_score REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)

    connection.commit()
    connection.close()


def add_job(title, description, skills, experience):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO jobs(title, description, required_skills, experience)
        VALUES (?, ?, ?, ?)
    """, (title, description, skills, experience))

    connection.commit()
    job_id = cursor.lastrowid
    connection.close()

    return job_id


def get_all_jobs():
    connection = get_connection()

    jobs = connection.execute("""
        SELECT * FROM jobs
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return jobs


def get_job(job_id):
    connection = get_connection()

    job = connection.execute("""
        SELECT * FROM jobs
        WHERE id = ?
    """, (job_id,)).fetchone()

    connection.close()

    return job


def add_candidate(
    job_id,
    name,
    email,
    phone,
    resume_filename,
    resume_text,
    match_score
):
    connection = get_connection()

    connection.execute("""
        INSERT INTO candidates(
            job_id,
            name,
            email,
            phone,
            resume_filename,
            resume_text,
            match_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        name,
        email,
        phone,
        resume_filename,
        resume_text,
        match_score
    ))

    connection.commit()
    connection.close()


def get_candidates(job_id):
    connection = get_connection()

    candidates = connection.execute("""
        SELECT *
        FROM candidates
        WHERE job_id = ?
        ORDER BY match_score DESC
    """, (job_id,)).fetchall()

    connection.close()

    return candidates


def get_candidate(candidate_id):
    connection = get_connection()

    candidate = connection.execute("""
        SELECT candidates.*, jobs.title AS job_title
        FROM candidates
        JOIN jobs ON candidates.job_id = jobs.id
        WHERE candidates.id = ?
    """, (candidate_id,)).fetchone()

    connection.close()

    return candidate


def update_candidate_status(candidate_id, status):
    connection = get_connection()

    connection.execute("""
        UPDATE candidates
        SET status = ?
        WHERE id = ?
    """, (status, candidate_id))

    connection.commit()
    connection.close()