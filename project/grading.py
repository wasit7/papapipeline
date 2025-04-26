import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import boto3
from botocore.client import Config
import logging

# Configuration
GITHUB_TOKEN = "your_github_token_here"
REPO_OWNER = "student_username"
REPO_NAME = "project_repo"
EXPECTED_REPO_NAME = "expected_project_name"
LAKEFS_ENDPOINT = "http://lakefs-dev:8000"
LAKEFS_ACCESS_KEY = "your_access_key"
LAKEFS_SECRET_KEY = "your_secret_key"
LAKEFS_REPO = "weather"
LAKEFS_BRANCH = "main"
PROJECT_START_DATE = datetime(2025, 4, 28)
EXPECTED_SCHEMA = {
    "timestamp": "datetime64[ns, UTC]",
    "year": "int64",
    "month": "int64",
    "day": "int64",
    "hour": "int64",
    "minute": "int64",
    "created_at": "object",
    "requested_province": "string",
    "location": "string",
    "weather_main": "string",
    "weather_description": "string",
    "main.temp": "float64",
    "humidity": "int64",
    "wind_speed": "float64"
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_repo_creation_date():
    """Get repository creation date via GitHub API."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    repo_data = response.json()
    return datetime.strptime(repo_data['created_at'], '%Y-%m-%dT%H:%M:%SZ')

def get_commit_info():
    """Get commit counts per week for the past three weeks."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, params={"since": PROJECT_START_DATE.isoformat()})
    response.raise_for_status()
    commits = response.json()
    weekly_commits = [0] * 3
    for commit in commits:
        commit_date = datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ')
        week_num = (commit_date - PROJECT_START_DATE).days // 7
        if 0 <= week_num < 3:
            weekly_commits[week_num] += 1
    return weekly_commits

def get_readme_info():
    """Get README character count."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/README.md"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 0
    readme_data = response.json()
    content = requests.get(readme_data['download_url']).text
    return len(content)

def load_flow_summary():
    """Load flow_summary.json from lakeFS."""
    s3 = boto3.client(
        's3',
        endpoint_url=LAKEFS_ENDPOINT,
        aws_access_key_id=LAKEFS_ACCESS_KEY,
        aws_secret_access_key=LAKEFS_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )
    try:
        obj = s3.get_object(Bucket=LAKEFS_REPO, Key=f"{LAKEFS_BRANCH}/reports/flow_summary.json")
        return json.loads(obj['Body'].read())
    except Exception as e:
        logger.error(f"Failed to load flow_summary.json: {e}")
        return None

def grade_repository():
    """Grade repository creation and naming. (10 marks)"""
    try:
        creation_date = get_repo_creation_date()
        first_week_end = PROJECT_START_DATE + timedelta(days=7)
        is_in_first_week = creation_date <= first_week_end
        is_correct_name = REPO_NAME == EXPECTED_REPO_NAME
        if is_in_first_week and is_correct_name:
            return 10, "Repository created on time with correct name."
        else:
            return 0, "Repository not created on time or incorrect name."
    except Exception as e:
        return 0, f"Error: {str(e)}"

def grade_commits():
    """Grade commit frequency. (10 marks)"""
    try:
        weekly_commits = get_commit_info()
        scores = [10 if count >= 5 else (count / 5) * 10 for count in weekly_commits]
        score = sum(scores) / len(scores)
        message = f"Weekly commits: {weekly_commits}"
        return score, message
    except Exception as e:
        return 0, f"Error: {str(e)}"

def grade_readme():
    """Grade README quality. (10 marks)"""
    try:
        char_count = get_readme_info()
        if char_count >= 1000:
            score = 10
        else:
            score = (char_count / 1000) * 10
        message = f"README characters: {char_count}"
        return score, message
    except Exception as e:
        return 0, f"Error: {str(e)}"

def grade_dataset(summary_data):
    """Grade dataset based on summary data. (40 marks)"""
    if summary_data is None:
        return 0, "No dataset summary found."
    
    scores = []
    messages = []
    
    # Record count (10 marks)
    if summary_data['overview']['record_count'] >= 1000:
        scores.append(10)
        messages.append("Sufficient record count.")
    else:
        scores.append(0)
        messages.append("Insufficient record count.")
    
    # Time span (10 marks)
    if summary_data['overview']['time_span_hours'] >= 24:
        scores.append(10)
        messages.append("Sufficient time span.")
    else:
        scores.append(0)
        messages.append("Insufficient time span.")
    
    # Completeness (10 marks)
    if summary_data['overview']['completeness'] >= 0.9:
        scores.append(10)
        messages.append("Data completeness meets requirements.")
    else:
        scores.append(0)
        messages.append("Data completeness below requirements.")
    
    # No object dtype (10 marks)
    if not summary_data['overview']['has_object_dtype']:
        scores.append(10)
        messages.append("No object data types found.")
    else:
        scores.append(0)
        messages.append("Object data types found.")
    
    # No duplicates (10 marks)
    if summary_data['overview']['duplicate_count'] == 0:
        scores.append(10)
        messages.append("No duplicate rows found.")
    else:
        scores.append(0)
        messages.append(f"{summary_data['overview']['duplicate_count']} duplicate rows found.")
    
    # Schema compliance (10 marks)
    if summary_data['schema_compliance']['overall_compliance'] == 100.0:
        scores.append(10)
        messages.append("Schema fully compliant.")
    else:
        scores.append(0)
        messages.append("Schema not fully compliant.")
    
    total_score = sum(scores)
    message = " | ".join(messages)
    return total_score, message

def generate_grading_summary():
    """Generate grading summary and save to grading_summary.json."""
    summary_data = load_flow_summary()
    repo_score, repo_message = grade_repository()
    commits_score, commits_message = grade_commits()
    readme_score, readme_message = grade_readme()
    dataset_score, dataset_message = grade_dataset(summary_data)
    
    grading_summary = {
        "overview": {
            "repository_score": repo_score,
            "commits_score": commits_score,
            "readme_score": readme_score,
            "dataset_score": dataset_score
        },
        "details": {
            "repository": repo_message,
            "commits": commits_message,
            "readme": readme_message,
            "dataset": dataset_message
        },
        "total": {
            "score": repo_score + commits_score + readme_score + dataset_score,
            "max_score": 70  # Adjusted for the number of criteria
        }
    }
    
    with open("grading_summary.json", "w") as f:
        json.dump(grading_summary, f, indent=2)
    
    return grading_summary

if __name__ == "__main__":
    results = generate_grading_summary()
    print(json.dumps(results, indent=2))