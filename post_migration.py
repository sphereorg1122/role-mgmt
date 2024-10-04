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

# Build system file indicators
build_systems = {
    'maven': 'pom.xml',
    'gradle': 'build.gradle',
    'npm': 'package.json',
    'yarn': 'yarn.lock',
    'make': 'Makefile',
    'cmake': 'CMakeLists.txt',
    'bazel': 'BUILD',
    'go': 'go.mod',
    'rust': 'Cargo.toml',
    'python_setuptools': 'setup.py',
    'python_pip': 'requirements.txt',
    'python_pyproject': 'pyproject.toml',
    'ruby_bundler': 'Gemfile',
    'ruby_gem': '.gemspec',
    'dotNET_CS': '.csproj',
    'dotNET_VB': '.vbproj',
    'dotNET_FS': '.fsproj',
    'dotNET_Solution': '.sln',
    'dotNET_SDK': 'global.json',
    'dotNET_NuGet': 'packages.config'
}

def load_repositories_from_csv(file_path):
    """Read repository names from a CSV file."""
    repos = []
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        repos = [row[0].strip() for row in reader if row]
    return repos

def detect_build_system(repo):
    """Detect the build system used in a GitHub repository."""
    try:
        contents = repo.get_contents("")
        repo_files = [content.path for content in contents]

        detected_build_systems = []
        for build_system, indicator_file in build_systems.items():
            if any(indicator_file in file for file in repo_files):
                detected_build_systems.append(build_system)

        build_systems_detected = ', '.join(detected_build_systems) if detected_build_systems else "No common build system detected."
        return build_systems_detected
    except Exception as e:
        print(f"Error detecting build system for repository {repo.full_name}: {e}")
        return "Error detecting build system"

def get_repo_details(repo_name):
    """Fetch repository details from GitHub."""
    try:
        repo = g.get_repo(repo_name)
        primary_language = repo.language
        repo_size = repo.size  # Size in KB
        branches = [branch.name for branch in repo.get_branches()]
        branch_count = len(branches)
        build_system = detect_build_system(repo)
        return {
            'repo_name': repo_name,
            'primary_language': primary_language,
            'branch_count': branch_count,
            'repo_size': repo_size,
            'branches': ', '.join(branches),
            'build_system': build_system
        }
    except Exception as e:
        print(f"Error fetching details for repository {repo_name}: {e}")
        return None

def log_post_migration_summary(source_repo, target_repo, source_details, target_details):
    """Log post-migration details to post_migration_summary.csv."""
    with open(post_migration_summary_csv, mode='a', newline='') as file:
        fieldnames = ['source_repo', 'target_repo', 'source_primary_language', 'target_primary_language',
                      'source_branch_count', 'target_branch_count', 'source_repo_size', 'target_repo_size',
                      'source_branches', 'target_branches', 'source_build_system', 'target_build_system', 'status']
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
            'source_build_system': source_details['build_system'],
            'target_build_system': target_details['build_system'],
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
