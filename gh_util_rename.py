import os
import datetime
import argparse
import logging
import requests
from github import Github
from github import GithubException

# repository input file delimiter 
INPUT_FILE_DELIMITER = ";"  

# GitHub API base URL 
GITHUB_BASE_API_URL = "https://api.github.com"

# Get source & target repositiroes from comma separated file , 
# <1 repo> DELIMITOR <2 repo> , <topic anme>   
def load_repositories_from_file(repo_file_path):
    repos = []
    try:
        with open(repo_file_path, "r", encoding='utf-8-sig') as file:
            for line in file:
                repo_detail, rename_branch_detail, default_branch = line.strip().split(INPUT_FILE_DELIMITER)
                repos.append((repo_detail, rename_branch_detail, default_branch))
    except Exception as e:
        log_and_print(f"...Error reading the file {repo_file_path}: {e}", "error")
    return repos

#  write to log file & same time print in console 
def log_and_print(message, log_level='info'):
    RED = '\033[31m'
    GREEN = '\033[32m'
    ORANGE = '\033[38;5;214m' 
    RESET = '\033[0m'
    # Get the current datetime with seconds
    log_datetime = datetime.datetime.now().strftime('%d%b%Y_%H%M%S')
    # Log the message to the file based on the log level
    if log_level == 'error':
        logging.error(f": {message}")
        print(f"{RED}{log_datetime}: {message} {RESET}") # Print the message to the console with the formatted datetime & color 
    elif log_level == 'success':
        logging.info(f":{message}")  
        print(f"{GREEN}{log_datetime}: {message} {RESET}") # Print the message to the console with the formatted datetime & color
    elif log_level == 'warning':
        logging.warning(f":{message}")  
        print(f"{ORANGE}{log_datetime}: {message} {RESET}") # Print the message to the console with the formatted datetime & color
    else:
        logging.info(f": {message}")
        print(f"{log_datetime}: {message}") # Print the message to the console with formatted datetime

# Rename GitHub branch with certificate validation
def rename_github_branch_with_cert_validation(repo_name, old_branch_name, new_branch_name, token, cert_path):
    api_url = f"{GITHUB_BASE_API_URL}/repos/{repo_name}/branches/{old_branch_name}/rename"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"new_name": new_branch_name}
    
    try:
        response = requests.get(f"{GITHUB_BASE_API_URL}/repos/{repo_name}/branches", headers=headers, verify=cert_path)
        response.raise_for_status()
        
        branches = [branch['name'] for branch in response.json()]

        # Check if both source and target branches exist, log error and skip
        if old_branch_name in branches and new_branch_name in branches:
            log_and_print(f"ERROR: Both '{old_branch_name}' and '{new_branch_name}' branches exist in {repo_name}. Skipping rename.", "error")
            return

        # If old branch exists, rename it
        if old_branch_name in branches:
            response = requests.post(api_url, headers=headers, json=payload, verify=cert_path)
            log_and_print(f"...{response}")
            
            if response.status_code in [200, 201]:
                log_and_print(f"...Successfully branch renamed : {old_branch_name} -> {new_branch_name}", "success")
            else:
                log_and_print(f"ERROR: Failed to rename branch: {response.status_code}", "error")
                log_and_print(response.json())
        else:
            log_and_print(f"WARNING: Source branch '{old_branch_name}' does not exist in {repo_name}. Skipping rename.", "warning")

    except requests.exceptions.SSLError as e:
        log_and_print(f"ERROR: SSL certificate validation failed: {e}", "error")
    except Exception as e:
        log_and_print(f"ERROR: An error occurred: {e}", "error")

# Setting the default branch
def set_default_branch(repo_name, default_branch, token, cert_path):
    api_url = f"{GITHUB_BASE_API_URL}/repos/{repo_name}/branches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        # First, check if the default branch exists
        response = requests.get(api_url, headers=headers, verify=cert_path)
        response.raise_for_status()

        branches = [branch['name'] for branch in response.json()]
        
        # Check if the default branch exists in the repository
        if default_branch not in branches:
            log_and_print(f"WARNING: The default branch '{default_branch}' does not exist in the repository '{repo_name}'. Skipping default branch update.", "warning")
            return

        # If the branch exists, proceed to set it as the default branch
        repo_api_url = f"{GITHUB_BASE_API_URL}/repos/{repo_name}"
        payload = {"default_branch": default_branch}
        
        # Update the default branch
        response = requests.patch(repo_api_url, headers=headers, json=payload, verify=cert_path)
        
        if response.status_code == 200:
            log_and_print(f"Successfully set '{default_branch}' as the default branch for '{repo_name}'", "success")
        else:
            log_and_print(f"Failed to set default branch: {response.status_code}", "error")
            log_and_print(response.json())
    
    except requests.exceptions.SSLError as e:
        log_and_print(f"SSL certificate validation failed: {e}", "error")
    except Exception as e:
        log_and_print(f"An error occurred while setting the default branch: {e}", "error")


def main():
    # Setup argument parser for command-line flags
    parser = argparse.ArgumentParser(description=f"...Process POST migration validation for repositories...")
    parser.add_argument('-r', '--repo_file', type=str, required=True, help="Path to the CSV file containing list of repositories")
    parser.add_argument('-o', '--output_folder', type=str, default='./output', help="Path to the folder where the migration summary will be saved (default: './output').")
    args = parser.parse_args()

    # Get the migration CSV filename from the argument
    list_repos_file_path = args.repo_file
    output_log_folder = args.output_folder

    # Get the current date and time, and format it
    current_datetime = datetime.datetime.now().strftime('%d%b%Y_%H%M')

    # GitHub connection for target repository
    SOURCE_GITHUB_TOKEN = os.getenv('SOURCE_GITHUB_TOKEN')
    SOURCE_CERT_PATH = os.getenv('SOURCE_CERT_PATH')
    if not SOURCE_GITHUB_TOKEN:
        raise ValueError("SOURCE_GITHUB_TOKEN environment variable not set.")

    # Get the input path of the filename from the argument
    list_repos_file_path = args.repo_file

    # Extract the base filename without the extension
    base_filename = os.path.splitext(os.path.basename(list_repos_file_path))[0]

    # migration summary details file 
    branchUtil_summary_filePath = f"./{output_log_folder}/RENAME_STATUS_{base_filename}_{current_datetime}.csv"

    # Log file name 
    migration_log_file = f"{output_log_folder}/LOG_{base_filename}_{current_datetime}.log"
    
    # Extract the directory part of the path
    log_directory = os.path.dirname(migration_log_file)
    
    # Check if the directory exists, and if not, create it
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Set up the logger
    logging.basicConfig(filename=f"{migration_log_file}", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log_and_print(f"... Input details file path = {list_repos_file_path}")

    repos_input_details = load_repositories_from_file(list_repos_file_path)
    # log_and_print(f" --- Input details  = {repos_input_details}")

    if not repos_input_details:
        log_and_print(f"...No repositories found in the file {list_repos_file_path}...", "error")
    else:
        for index, (repo_detail, branch_mapping, default_branch) in enumerate(repos_input_details, start=1):
            try:
                log_and_print(f"{index}...Renaming branches at Repo : '{repo_detail}' ; branch_mapping:{branch_mapping}  ")

                # Split branch_mapping into multiple mappings (master=main, dev2=develop)
                branch_mappings = branch_mapping.split(",")
                
                for mapping in branch_mappings:
                    old_branch, new_branch = mapping.split("=")
                    log_and_print(f"...Renaming the Branch '{old_branch}' to '{new_branch}' Start...")
                    
                    # Rename the branch using GitHub API
                    rename_github_branch_with_cert_validation(repo_detail, old_branch, new_branch, SOURCE_GITHUB_TOKEN, SOURCE_CERT_PATH)
                    log_and_print(f"...Completed Renaming the Branch '{old_branch}' to '{new_branch}' at Repo : '{repo_detail}'")

            except Exception as e:
                log_and_print(f"{index}...Failed to rename branch at Repo : '{repo_detail}' due to error: {str(e)}")
            
            try:
                log_and_print(f"{index}...Setting default branch '{default_branch}' at Repo : '{repo_detail}' ")
                # You can add the logic to set the default branch here
                set_default_branch(repo_detail, default_branch, SOURCE_GITHUB_TOKEN, SOURCE_CERT_PATH)

            except Exception as e:
                log_and_print(f"{index}...Failed to set default branch at Repo : '{repo_detail}' due to error: {str(e)}")

    log_and_print("********* Branch Utitily Process Completed... Review Status & log file for further actions... *********")

if __name__ == '__main__':
    main()
