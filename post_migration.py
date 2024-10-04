import os
import csv
from github import Github

# Input CSV files
source_repos_csv = "source_repos.csv"
target_repos_csv = "target_repos.csv"
post_migration_summary_csv = "post_migration_summary.csv"

# GitHub connection
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set.")
g = Github(GITHUB_TOKEN)

def load_repositories_from_csv(file_path):
    """Read repository names from a CSV file."""
    repos = []
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        repos = [row[0].strip() for row in reader if row]
    return repos

def get_repo_details(repo_name):
    """Fetch repository details from GitHub."""
    try:
        repo = g.get_repo(repo_name)
        primary_language = repo.language
        repo_size = repo.size  # Size in KB
        branches = [branch.name for branch in repo.get_branches()]
        branch_count = len(branches)
        return {
            'repo_name': repo_name,
            'primary_language': primary_language,
            'branch_count': branch_count,
            'repo_size': repo_size,
            'branches': ', '.join(branches)
        }
    except Exception as e:
        print(f"Error fetching details for repository {repo_name}: {e}")
        return None

def log_post_migration_summary(source_repo, target_repo, source_details, target_details):
    """Log post-migration details to post_migration_summary.csv."""
    with open(post_migration_summary_csv, mode='a', newline='') as file:
        fieldnames = ['source_repo', 'target_repo', 'source_primary_language', 'target_primary_language',
                      'source_branch_count', 'target_branch_count', 'source_repo_size', 'target_repo_size',
                      'source_branches', 'target_branches', 'status']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if file.tell() == 0:  # Write header only if file is empty
            writer.writeheader()

        status = "Match" if source_details['branch_count'] == target_details['branch_count'] and source_details['repo_size'] == target_details['repo_size'] else "Mismatch"

        writer.writerow({
            'source_repo': source_repo,
            'target_repo': target_repo,
            'source_primary_language': source_details['primary_language'],
            'target_primary_language': target_details['primary_language'],
            'source_branch_count': source_details['branch_count'],
            'target_branch_count': target_details['branch_count'],
            'source_repo_size': source_details['repo_size'],
            'target_repo_size': target_details['repo_size'],
            'source_branches': source_details['branches'],
            'target_branches': target_details['branches'],
            'status': status
        })

if __name__ == "__main__":
    # Load repositories from CSV files
    source_repos = load_repositories_from_csv(source_repos_csv)
    target_repos = load_repositories_from_csv(target_repos_csv)

    if len(source_repos) != len(target_repos):
        print("Mismatch in the number of source and target repositories.")
    else:
        # Process each pair of source and target repos
        for source_repo, target_repo in zip(source_repos, target_repos):
            print(f"Processing post-migration for Source: {source_repo} -> Target: {target_repo}")

            # Get details from both source and target repositories
            source_details = get_repo_details(source_repo)
            target_details = get_repo_details(target_repo)

            if source_details and target_details:
                log_post_migration_summary(source_repo, target_repo, source_details, target_details)
                print(f"Logged post-migration summary for {source_repo} -> {target_repo}.")
            else:
                print(f"Skipping {source_repo} -> {target_repo} due to missing details.")
