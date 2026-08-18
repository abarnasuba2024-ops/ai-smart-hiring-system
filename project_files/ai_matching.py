from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_score(job_text, resume_text):

    if not job_text or not resume_text:
        return 0.0

    documents = [
        job_text.lower(),
        resume_text.lower()
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    try:
        matrix = vectorizer.fit_transform(documents)

        similarity = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0]

        score = similarity * 100

        return round(score, 2)

    except Exception as e:
        print("AI matching error:", e)

        return 0.0


def get_recommendation(score):

    if score >= 80:
        return "Highly Recommended"

    elif score >= 60:
        return "Recommended"

    elif score >= 40:
        return "Consider"

    else:
        return "Not Recommended"