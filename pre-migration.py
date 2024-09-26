import os
import shutil
import subprocess
import requests  # Added for the API call
from github import Github
import csv
import time

# GitHub Personal Access Token from environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set.")

# Initialize GitHub connection for other operations
g = Github(GITHUB_TOKEN)

# Organization name where the repositories should be created
ORG_NAME = "capgemini-cigna-demo"

# GitHub repo where the CI templates are stored
CI_TEMPLATE_REPO = "capgemini-ga-demo/github_centralized_workflows"
CI_TEMPLATE_BRANCH = "develop"
CI_TEMPLATE_PATH = "templates"

# CSV file path
csv_file_path = "migration_log.csv"


def get_repo_size_via_api(repo_name, access_token):
    """Fetch repository size using GitHub API."""
    api_url = f"https://api.github.com/repos/{repo_name}"
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

        # Parse the response JSON and get the size
        repo_data = response.json()
        repo_size = repo_data.get('size')  # Size is in KB

        if repo_size is not None:
            print(f"Repository {repo_name} size: {repo_size} KB")
            return repo_size
        else:
            print(f"Repository size not found for {repo_name}")
            return 0
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repository data: {e}")
        return 0


def print_separator_with_repo_name(repo_name, phase="Starting migration"):
    """Prints a separator line with the repo_name in the middle."""
    total_length = 100  # Total length of the line including equal signs and repo_name
    repo_display = f" {phase} for {repo_name} "  # Add spaces for padding around repo_name
    num_equals = total_length - len(repo_display)

    # Ensure equal signs are evenly distributed on both sides
    left_equals = num_equals // 2
    right_equals = num_equals - left_equals

    print(f"\n{'=' * left_equals}{repo_display}{'=' * right_equals}\n")


def detect_language_and_build_system(repo_name):
    """Detect the primary language and the build system used in a GitHub repository."""
    try:
        repo = g.get_repo(repo_name)
        primary_language = repo.language

        contents = repo.get_contents("")
        repo_files = [content.path for content in contents]

        detected_build_systems = []
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

        for build_system, indicator_file in build_systems.items():
            if any(indicator_file in file for file in repo_files):
                detected_build_systems.append(build_system)

        build_systems_detected = ', '.join(detected_build_systems) if detected_build_systems else "No common build system detected."

        return primary_language, build_systems_detected
    except Exception as e:
        print(f"Error fetching repository data for {repo_name}: {e}")
        return None, None


def create_or_update_repo(repo_name):
    """Create or update a repository in the specified organization."""
    try:
        repo = g.get_organization(ORG_NAME).get_repo(repo_name)
        print(f"Repository '{repo_name}' already exists. Updating...")
        return repo
    except Exception:
        try:
            print(f"Creating repository '{repo_name}' under organization '{ORG_NAME}'...")
            repo = g.get_organization(ORG_NAME).create_repo(repo_name)
            print(f"\033[92mRepository '{repo.name}' created successfully.\033[0m")  # Green for success
            return repo
        except Exception as e:
            print(f"Error creating repository '{repo_name}': {e}")
            return None


def push_branches_and_tags(local_repo_path, push_url):
    """Push the branches and tags, excluding problematic refs like pull requests."""
    try:
        # Remove any existing remote origin, then add the new one
        subprocess.run(['git', 'remote', 'rm', 'origin'], cwd=local_repo_path, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin', push_url], cwd=local_repo_path, check=True)

        # Push branches and tags, excluding problematic refs like pull requests
        print(f"  - Pushing branches and tags to '{push_url}'...")
        subprocess.run(['git', 'push', '--all'], cwd=local_repo_path, check=True)  # Push all branches
        subprocess.run(['git', 'push', '--tags'], cwd=local_repo_path, check=True)  # Push all tags

    except subprocess.CalledProcessError as e:
        print(f"Error pushing branches and tags: {e}")


def log_migration_to_csv(source_url, target_url, migrated_with_workflow, source_size, source_branches, dest_size, dest_branches):
    """Log migration details to a CSV file without creating duplicate entries."""
    file_exists = os.path.isfile(csv_file_path)

    # Read existing entries to check for duplicates
    existing_entries = []
    if file_exists:
        with open(csv_file_path, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                existing_entries.append(row['source_github_url'])

    # Only log the entry if it doesn't already exist
    if source_url not in existing_entries:
        with open(csv_file_path, mode='a', newline='') as csv_file:
            fieldnames = ['source_github_url', 'target_github_url', 'migrated_with_workflow_file', 'source_branch_count',
                          'source_repo_size_kb', 'destination_branch_count', 'destination_repo_size_kb']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write header only if the file doesn't exist
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'source_github_url': source_url,
                'target_github_url': target_url,
                'migrated_with_workflow_file': migrated_with_workflow,
                'source_branch_count': source_branches,
                'source_repo_size_kb': source_size,
                'destination_branch_count': dest_branches,
                'destination_repo_size_kb': dest_size
            })
        print(f"Logged migration for {source_url} to {target_url}.")
    else:
        print(f"Duplicate entry detected for {source_url}. Skipping logging.")


if __name__ == "__main__":
    # Replace 'your-access-token' with your actual GitHub access token
    access_token = GITHUB_TOKEN

    file_path = "repos.txt"  # Replace with your file path
    repos = []

    # Load repositories from file
    try:
        with open(file_path, "r") as file:
            repos = [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Error reading the file: {e}")

    if not repos:
        print("No repositories found in the file.")
    else:
        for repo_name in repos:
            print_separator_with_repo_name(repo_name, phase="Starting migration")

            primary_language, build_system = detect_language_and_build_system(repo_name)
            if primary_language and build_system:
                print(f"Repository: {repo_name}")
                print(f"  - Primary Language: {primary_language}")
                print(f"  - Build System(s): {build_system}")

                # Fetch the size of the source repo using API
                source_size = get_repo_size_via_api(repo_name, access_token)

                # Fetch details for the destination repo
                dest_repo_name = f"{ORG_NAME}/{repo_name.split('/')[-1]}"
                dest_size = get_repo_size_via_api(dest_repo_name, access_token)

                # Log the migration details
                log_migration_to_csv(f'https://github.com/{repo_name}.git', f'https://github.com/{dest_repo_name}.git',
                                     True, source_size, 0, dest_size, 0)

                print_separator_with_repo_name(repo_name, phase="End of migration")
