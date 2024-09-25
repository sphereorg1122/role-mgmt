import os
import shutil
import subprocess
from github import Github

# GitHub Personal Access Token from environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set.")

# Initialize GitHub connection
g = Github(GITHUB_TOKEN)

# Organization name where the repositories should be created
ORG_NAME = "capgemini-cigna-demo"

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

# Directory path for checking build system CI files
ci_directory = 'github_centralized_workflows'  # Assuming github_centralized_workflows is in the root of the repository

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

def check_ci_file_exists(ci_directory, build_system):
    """Check if a CI file for the build system exists in the given directory."""
    ci_file = os.path.join(ci_directory, f"{build_system}-ci.yml")
    return ci_file if os.path.exists(ci_file) else None

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
            print(f"Repository '{repo.name}' created successfully.")
            return repo
        except Exception as e:
            print(f"Error creating repository '{repo_name}': {e}")
            return None

if __name__ == "__main__":
    file_path = "repos.txt"  # Replace with your file path
    
    repos = load_repositories_from_file(file_path)
    
    if not repos:
        print("No repositories found in the file.")
    else:
        for repo_name in repos:
            primary_language, build_system = detect_language_and_build_system(repo_name)
            if primary_language and build_system:
                print(f"Repository: {repo_name}")
                print(f"  - Primary Language: {primary_language}")
                print(f"  - Build System(s): {build_system}")
                
                build_system_list = build_system.split(', ')  
                for system in build_system_list:
                    ci_file_path = check_ci_file_exists(ci_directory, system.strip())
                    if ci_file_path:
                        print(f"  - CI File Found: {ci_file_path}")
                        
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
                            print(f"  - Pushing to '{push_url}'...")
                            try:
                                subprocess.run(['git', 'push', '--mirror', push_url], cwd=local_repo_path, check=True)
                            except subprocess.CalledProcessError as e:
                                print(f"Error pushing to repository: {e}")
                                continue
                            
                            print(f"  - Moving CI file to '{local_repo_name}-repo/.github/workflows/'...")
                            os.makedirs(os.path.join(local_repo_path, '.github', 'workflows'), exist_ok=True)
                            shutil.copy(ci_file_path, os.path.join(local_repo_path, '.github', 'workflows'))

                            # Clean up the local repo after push
                            try:
                                shutil.rmtree(local_repo_path)
                            except Exception as e:
                                os.system(f'rmdir /S /Q "{local_repo_path}"')
                            

                            print(f"  - Migration complete for repository: {repo_name}\n")
                        else:
                            print(f"Failed to create or update repository '{local_repo_name}' in organization '{ORG_NAME}'.")
                    else:
                        print(f"  - No matching CI file found for {system.strip()} in {ci_directory}")
                print()
            else:
                print(f"Could not determine the language or build system for repository: {repo_name}")
