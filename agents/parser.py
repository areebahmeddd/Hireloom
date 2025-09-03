import os
import re
import json
import PyPDF2
import google.generativeai as genai
from github import Github, Auth
from dotenv import load_dotenv
from agents.database import upload_to_firestore

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("Gemini API key is required")

genai.configure(api_key=gemini_key)
ai_model = genai.GenerativeModel("gemini-2.5-flash")


def parse_resume(job_description, pdf_path):
    resume_text = read_pdf(pdf_path)
    clean_text = clean_data(resume_text)

    name = get_name(resume_text)
    email = get_email(resume_text)
    phone = get_phone(resume_text)
    linkedin = get_linkedin(resume_text)
    github_link = get_github(resume_text)

    analysis = analyze_ai(job_description, clean_text)
    github_data = None
    user = find_github(resume_text)
    if user:
        job_words = job_description.split()
        github_data = get_projects(user, job_words)

    summary = make_summary(github_data)
    score = score_candidate(job_description, clean_text, summary)

    contact_info = {
        "email": email,
        "linkedin": linkedin,
        "github": github_link,
        "phone": phone,
    }

    result = {
        "candidate_name": person_name,
        "resume_analysis": analysis,
        "contact_info": contact_data,
        "github_analysis": github_data,
        "combined_score": final_score,
    }

    doc_id = upload_to_firestore(result)
    return [result]
def extract_phone(resume_text):
    match = re.search(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}", resume_text)
    return match.group(0) if match else None

def extract_email(resume_text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
    return match.group(0) if match else None

def extract_linkedin(resume_text):
        match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", resume_text)
        if match:
            # Ensure full URL
            url = match.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
        # Also match linkedin.com/<username>
        match2 = re.search(r"(https?://)?(www\.)?linkedin\.com/[a-zA-Z0-9_-]+", resume_text)
        if match2:
            url = match2.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
        return None

def extract_github_link(resume_text):
        match = re.search(r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+", resume_text)
        if match:
            url = match.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
        return None


def extract_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF file: {str(e)}")
    return text


def clean_data(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,;:!?@#%&*+/-]", "", text)
    return text.strip()


def get_name(resume_text):
    lines = resume_text.split("\n")
    first_lines = " ".join(lines[:3])

    patterns = [
        r"^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:Name|Full Name):\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, first_lines)
        if matches:
            return matches[0].strip()

    return "Unknown Person"


def get_phone(resume_text):
    match = re.search(
        r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}", resume_text
    )
    return match.group(0) if match else None


def get_email(resume_text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
    return match.group(0) if match else None


def get_linkedin(resume_text):
    match = re.search(
        r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", resume_text
    )
    if match:
        url = match.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        return url

    match2 = re.search(r"(https?://)?(www\.)?linkedin\.com/[a-zA-Z0-9_-]+", resume_text)
    if match2:
        url = match2.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None


def get_github(resume_text):
    match = re.search(r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+", resume_text)
    if match:
        url = match.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None


def analyze_ai(job_description, resume_text):
    prompt = f"""
    Analyze this resume against the given job description and provide a comprehensive evaluation.

    JOB DESCRIPTION:
    {job_description}

    RESUME:
    {resume_text}

    Please provide a JSON response with the following structure:
    {{
        "skills_match": {{
            "matched_skills": [],
            "missing_skills": []
        }},
        "experience_evaluation": {{
            "years_experience": 0,
            "relevance": "low/medium/high"
        }},
        "education_evaluation": {{
            "degree_match": true/false,
            "education_level": "High School/Bachelor's/Master's/PhD/Other"
        }},
        "strengths": [],
        "weaknesses": [],
        "overall_assessment": "text summary"
    }}

    Be objective and focus on factual matches between the resume and job requirements.
    """

    try:
        response = ai_model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                "skills_match": {"matched_skills": [], "missing_skills": []},
                "experience_evaluation": {"years_experience": 0, "relevance": "low"},
                "education_evaluation": {"degree_match": False, "education_level": ""},
                "keyword_analysis": {"matched_keywords": [], "missing_keywords": []},
                "strengths": [],
                "weaknesses": [],
                "overall_assessment": "Failed to parse response",
            }
    except Exception as e:
        raise Exception(f"Error calling Gemini API: {str(e)}")


def find_github(resume_text):
    matches = re.findall(r"github\.com/([A-Za-z0-9_-]+)", resume_text)
    if matches:
        return matches[0]

    matches = re.findall(r"https?://github\.com/([A-Za-z0-9_-]+)", resume_text)
    if matches:
        return matches[0]

    return None


def get_projects(github_user, job_words):
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    client = Github(auth=auth)

    try:
        user = client.get_user(github_user)
        repos = user.get_repos()
        relevant_repos = []

        for repo in repos:
            try:
                languages = list(repo.get_languages().keys())
            except Exception:
                languages = []

            repo_data = {
                "name": repo.name,
                "description": repo.description,
                "languages": languages,
            }

            if any(
                kw.lower() in (repo.description or "").lower()
                or kw.lower() in (repo.language or "").lower()
                for kw in job_words
            ):
                relevant_repos.append(repo_data)

        return {"total_repos": repos.totalCount, "relevant_repos": relevant_repos}
    except Exception as e:
        return {"error": str(e)}


def make_summary(data):
    if not data or "error" in data:
        return "No valid GitHub data."

    summary = f"Total Public Repos: {data.get('total_repos', 'N/A')}\n"
    for repo in data.get("relevant_repos", []):
        summary += f"Project: {repo['name']}\nDescription: {repo['description']}\nLanguages: {', '.join(repo['languages'])}\n---\n"
    return summary


def score_candidate(job_description, resume_text, github_info):
    prompt = (
        f"Analyze the following candidate for suitability for the job. Consider both resume and GitHub profile data.\n\n"
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"RESUME:\n{resume_text}\n\n"
        f"GITHUB PROFILE DATA:\n{github_info}\n\n"
        "Provide a JSON response with:\n{\n  'suitability_score': 0-100,\n  'github_score': 0-100,\n  'resume_score': 0-100\n}\n"
    )

    try:
        response = ai_model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                "suitability_score": 0,
                "github_score": 0,
                "resume_score": 0,
            }
    except Exception:
        return {
            "suitability_score": 0,
            "github_score": 0,
            "resume_score": 0,
        }
