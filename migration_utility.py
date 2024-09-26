import os
import shutil
import subprocess
from github import Github
import csv

# GitHub Personal Access Token from environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set.")

# Initialize GitHub connection
g = Github(GITHUB_TOKEN)

# Organization name where the repositories should be created
ORG_NAME = "capgemini-cigna-demo"

# GitHub repo where the CI templates are stored
CI_TEMPLATE_REPO = "capgemini-ga-demo/github_centralized_workflows"
CI_TEMPLATE_BRANCH = "develop"
CI_TEMPLATE_PATH = "templates"

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

# CSV file path
csv_file_path = "migration_log.csv"

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
        for build_system, indicator_file in build_systems.items():
            if any(indicator_file in file for file in repo_files):
                detected_build_systems.append(build_system)
        
        build_systems_detected = ', '.join(detected_build_systems) if detected_build_systems else "No common build system detected."

        return primary_language, build_systems_detected
    except Exception as e:
        print(f"Error fetching repository data for {repo_name}: {e}")
        return None, None

def load_repositories_from_file(file_path):
    """Read repository names from a file."""
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Error reading the file: {e}")
        return []

def fetch_ci_file_from_github(build_system):
    """Fetch the CI template from the Centralized Workflow repository."""
    try:
        repo = g.get_repo(CI_TEMPLATE_REPO)
        ci_file_path = f"{CI_TEMPLATE_PATH}/{build_system}-ci.yml"

        # Fetch the content if the file exists
        ci_file = repo.get_contents(ci_file_path, ref=CI_TEMPLATE_BRANCH)
        return ci_file.decoded_content.decode('utf-8')
    
    except Exception as e:
        print(f"Error fetching Centralized Workflow File for {build_system}: {e}")
        return None

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

def log_migration_to_csv(source_url, target_url, migrated_with_workflow):
    """Log migration details to a CSV file."""
    file_exists = os.path.isfile(csv_file_path)
    
    with open(csv_file_path, mode='a', newline='') as csv_file:
        fieldnames = ['source_github_url', 'target_github_url', 'migrated_with_workflow_file']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # Write header only if the file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'source_github_url': source_url,
            'target_github_url': target_url,
            'migrated_with_workflow_file': migrated_with_workflow
        })

if __name__ == "__main__":
    file_path = "repos.txt"  # Replace with your file path
    
    repos = load_repositories_from_file(file_path)
    
    if not repos:
        print("No repositories found in the file.")
    else:
        for repo_name in repos:
            # Add a separator and indicate the start of migration
            print_separator_with_repo_name(repo_name, phase="Starting migration")

            primary_language, build_system = detect_language_and_build_system(repo_name)
            if primary_language and build_system:
                print(f"Repository: {repo_name}")
                print(f"  - Primary Language: {primary_language}")
                print(f"  - Build System(s): {build_system}")
                
                build_system_list = build_system.split(', ')  
                ci_found = False
                ci_content = None
                for system in build_system_list:
                    ci_content = fetch_ci_file_from_github(system.strip())
                    if ci_content:
                        ci_found = True
                        print(f"\033[92m  - Centralized Workflow File Found for {system.strip()} from Centralized Workflow Repository\033[0m")  # Green for success
                        break  # Stop after finding the first valid Centralized Workflow File
                    else:
                        # Only print one error message for missing CI file
                        print(f"\033[91m  - Centralized Workflow File {system.strip()}-ci.yml does not exist in Centralized Workflow Repository.\033[0m")  # Red for failure

                # Proceed with the repository migration regardless of Centralized Workflow File existence
                local_repo_name = repo_name.split('/')[-1]  
                local_repo_path = os.path.join(os.getcwd(), f"{local_repo_name}-repo")

                if os.path.exists(local_repo_path):
                    print(f"  - Directory '{local_repo_name}-repo' already exists. Removing it.")
                    try:
                        shutil.rmtree(local_repo_path)
                    except Exception as e:
                        print(f"  - Error removing directory: {e}")
                        os.system(f'rmdir /S /Q "{local_repo_path}"')

                print(f"  - Cloning the repository to '{local_repo_name}-repo'...")
                subprocess.run(['git', 'clone', '--mirror', f'https://github.com/{repo_name}.git', local_repo_path], check=True)

                repo = create_or_update_repo(local_repo_name)

                if repo:
                    push_url = f'https://github.com/{ORG_NAME}/{local_repo_name}.git'
                    push_branches_and_tags(local_repo_path, push_url)

                    # If CI content was fetched, save it to the repo
                    if ci_found and ci_content:
                        print(f"  - Saving Centralized Workflow File to '{local_repo_name}-repo/.github/workflows/'...")
                        workflow_dir = os.path.join(local_repo_path, '.github', 'workflows')
                        os.makedirs(workflow_dir, exist_ok=True)
                        ci_file_path = os.path.join(workflow_dir, f"{system.strip()}-ci.yml")
                        with open(ci_file_path, 'w') as ci_file:
                            ci_file.write(ci_content)

                    # Log the migration details
                    source_url = f'https://github.com/{repo_name}.git'
                    target_url = push_url
                    log_migration_to_csv(source_url, target_url, ci_found)

                    # Clean up the local repo after push
                    try:
                        shutil.rmtree(local_repo_path)
                    except Exception as e:
                        os.system(f'rmdir /S /Q "{local_repo_path}"')

                    print(f"\033[92m  - Migration complete for repository: {repo_name}\033[0m")  # Green for success
                else:
                    print(f"\033[91mFailed to create or update repository '{local_repo_name}' in organization '{ORG_NAME}'.\033[0m")  # Red for failure

            else:
                print(f"\033[91mCould not determine the language or build system for repository: {repo_name}\033[0m")  # Red for failure

            # End of migration, add another separator
            print_separator_with_repo_name(repo_name, phase="End of migration")
