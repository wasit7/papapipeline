from datetime import datetime, timedelta
import json

# Configuration constants
CONFIG = {
    "project_start_date": "2023-10-01T00:00:00+00:00",
    "expected_repo_name": "project_repo",
    "min_record_count": 1000,
    "min_time_span_hours": 24,
    "min_completeness": 0.9,
    "min_readme_chars": 1000,
    "commits_per_week_full_score": 5
}

def check_minimum(value, threshold):
    """Utility function to check if a value meets a minimum threshold."""
    return 10 if value >= threshold else 0

def calculate_commit_score(commits, full_score_threshold):
    """Calculate average commit score across weeks."""
    scores = [min(10, (commit["count"] / full_score_threshold) * 10) for commit in commits]
    return sum(scores) / len(scores) if scores else 0

def final_grading(flow_summary, grading_summary):
    """
    Compute final grading scores based on flow_summary and grading_summary data.
    
    Args:
        flow_summary (dict): Dataset summary data.
        grading_summary (dict): Project summary data.
    
    Returns:
        dict: Scores for each criterion and total score.
    """
    results = {}

    # Repository grading
    repo = grading_summary["project"]["repository"]
    creation_date = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
    start_date = datetime.fromisoformat(CONFIG["project_start_date"])
    is_in_first_week = creation_date <= start_date + timedelta(days=7)
    is_correct_name = repo["name"] == CONFIG["expected_repo_name"]
    results["repository"] = 10 if is_in_first_week and is_correct_name else 0

    # Commits grading
    results["commits"] = calculate_commit_score(
        grading_summary["project"]["commits"],
        CONFIG["commits_per_week_full_score"]
    )

    # README grading
    char_count = grading_summary["project"]["readme"]["character_count"]
    results["readme"] = min(10, (char_count / CONFIG["min_readme_chars"]) * 10)

    # Dataset grading
    dataset = flow_summary["dataset"]
    results["record_count"] = check_minimum(dataset["record_count"], CONFIG["min_record_count"])
    results["time_span"] = check_minimum(dataset["time_range"]["duration_hours"], CONFIG["min_time_span_hours"])
    results["completeness"] = check_minimum(dataset["completeness"]["timestamp_completeness"], CONFIG["min_completeness"])
    results["no_object_dtype"] = 10 if not dataset["data_types"]["has_object_dtype"] else 0
    results["no_duplicates"] = 10 if dataset["duplicates"]["row_level_duplicate_count"] == 0 else 0
    results["schema_compliance"] = 10 if flow_summary["schema"]["compliance"]["overall"] == 100.0 else 0

    # Total score
    results["total"] = sum(results.values())

    return results

# Example usage
if __name__ == "__main__":
    with open("flow_summary.json", "r") as f:
        flow_data = json.load(f)
    with open("grading_summary.json", "r") as f:
        grading_data = json.load(f)
    
    scores = final_grading(flow_data, grading_data)
    print("Grading Results:", scores)