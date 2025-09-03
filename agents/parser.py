import os
import re
import json
import PyPDF2
import google.generativeai as genai
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("Gemini API key is required")

genai.configure(api_key=gemini_key)
ai_model = genai.GenerativeModel("gemini-2.5-flash")


def parse_resume(job_desc, pdf_path):
    print("Extracting text from document")
    resume_text = extract_pdf(pdf_path)
    print(f"Extracted {len(resume_text)} characters")

    print("Cleaning text content")
    clean_text = clean_data(resume_text)
    person_name = extract_name(resume_text)

    print("Sending resume to Gemini for analysis")
    analysis = analyze_gemini(job_desc, clean_text)
    print("Resume analysis completed")

    print("Searching for GitHub profile")
    github_user = find_github(resume_text)
    github_data = None
    if github_user:
        print(f"Found username: {github_user}")
        job_words = job_desc.split()
        github_data = get_projects(github_user, job_words)
        print("Repository analysis completed")
    else:
        print("No GitHub profile found")

    print("Creating GitHub summary")
    github_info = create_summary(github_data)

    print("Combining resume and GitHub scores")
    final_score = combine_scores(job_desc, clean_text, github_info)

    return {
        person_name: {
            "resume_analysis": analysis,
            "github_analysis": github_data,
            "combined_score": final_score,
        }
    }


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


def extract_name(resume_text):
    lines = resume_text.split("\n")
    first_lines = " ".join(lines[:3])

    name_patterns = [
        r"^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:Name|Full Name):\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
    ]

    for pattern in name_patterns:
        matches = re.findall(pattern, first_lines)
        if matches:
            return matches[0].strip()

    return "Unknown Person"


def analyze_gemini(job_desc, resume_text):
    prompt = f"""
    Analyze this resume against the given job description and provide a comprehensive evaluation.

    JOB DESCRIPTION:
    {job_desc}

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
        print("Calling Gemini API")
        response = ai_model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            print("JSON parsed successfully")
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
    # Pattern 1: github.com/username
    matches = re.findall(r"github\.com/([A-Za-z0-9_-]+)", resume_text)
    if matches:
        return matches[0]

    # Pattern 2: Full GitHub URL
    matches = re.findall(r"https?://github\.com/([A-Za-z0-9_-]+)", resume_text)
    if matches:
        return matches[0]

    return None


def get_projects(github_user, job_words):
    print(f"Connecting to GitHub API for user: {github_user}")
    github_token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(github_token)
    git_client = Github(auth=auth)

    try:
        user = git_client.get_user(github_user)
        repos = user.get_repos()
        relevant_repos = []

        print("Analyzing repositories")
        repo_count = 0
        for repo in repos:
            repo_count += 1

            try:
                languages = list(repo.get_languages().keys())
            except Exception:
                languages = []

            repo_data = {
                "name": repo.name,
                "description": repo.description,
                "languages": languages,
            }

            # Check if repo is relevant to job
            if any(
                kw.lower() in (repo.description or "").lower()
                or kw.lower() in (repo.language or "").lower()
                for kw in job_words
            ):
                relevant_repos.append(repo_data)

        print(f"Found {len(relevant_repos)} relevant repos out of {repo_count} total")
        return {"total_repos": repos.totalCount, "relevant_repos": relevant_repos}
    except Exception as e:
        return {"error": str(e)}


def create_summary(github_data):
    if not github_data or "error" in github_data:
        return "No valid GitHub data."

    summary = f"Total Public Repos: {github_data.get('total_repos', 'N/A')}\n"
    for repo in github_data.get("relevant_repos", []):
        summary += f"Project: {repo['name']}\nDescription: {repo['description']}\nLanguages: {', '.join(repo['languages'])}\n---\n"
    return summary


def combine_scores(job_desc, resume_text, github_info):
    prompt = (
        f"Analyze the following candidate for suitability for the job. Consider both resume and GitHub profile data.\n\n"
        f"JOB DESCRIPTION:\n{job_desc}\n\n"
        f"RESUME:\n{resume_text}\n\n"
        f"GITHUB PROFILE DATA:\n{github_info}\n\n"
        "Provide a JSON response with:\n{\n  'suitability_score': 0-100,\n  'github_score': 0-100,\n  'resume_score': 0-100\n}\n"
    )

    try:
        print("Calling Gemini for combined analysis")
        response = ai_model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            print("Combined scores calculated successfully")
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


if __name__ == "__main__":
    job_desc = """
    We are seeking a motivated Junior Machine Learning Engineer with:
    -A Bachelor's degree in Computer Science, Data Science, or a related field
    -Strong foundational knowledge of Machine Learning algorithms and principles
    -Proficiency in Python and key ML libraries (e.g., Scikit-learn, TensorFlow, or PyTorch)
    -Experience with data preprocessing, visualization, and analysis (Pandas, NumPy, Matplotlib)
    -Familiarity with version control systems, preferably Git
    -Strong problem-solving abilities and a passion for innovation
    -Excellent communication skills and ability to work in a collaborative team environment
    """

    try:
        print("Starting resume analysis")
        result = parse_resume(job_desc, r"data/resume.pdf")
        person_name = list(result.keys())[0]

        safe_filename = person_name.replace(" ", "-").lower()
        filename = f"{safe_filename}_resume.json"

        with open(filename, "w") as f:
            json.dump(result, f, indent=2)

        print("Analysis completed successfully")
    except Exception as e:
        print(f"Error: {str(e)}")
