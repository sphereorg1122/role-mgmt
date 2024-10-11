import re
import csv
import os
import subprocess
import sys

def parse_terraform_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    variable_block_pattern = r'variable\s+"(\w+)"\s+{([^}]*)}'
    provider_block_pattern = r'provider\s+"(\w+)"\s+{([^}]*)}'
    attribute_pattern = r'(\w+)\s*=\s*(.+)'

    variables = {}
    providers = {}

    for match in re.finditer(variable_block_pattern, content, re.DOTALL):
        var_name, var_content = match.groups()
        var_attributes = {}
        for attr_match in re.finditer(attribute_pattern, var_content):
            attr_name, attr_value = attr_match.groups()
            # Remove everything after and including '#'
            attr_value = attr_value.split('#')[0].strip()
            # Preserve quotes if they exist
            if attr_value.startswith('"') and attr_value.endswith('"'):
                var_attributes[attr_name.strip()] = attr_value
            else:
                var_attributes[attr_name.strip()] = attr_value.strip('"')
        variables[var_name] = var_attributes

    for match in re.finditer(provider_block_pattern, content, re.DOTALL):
        provider_name, provider_content = match.groups()
        provider_attributes = {}
        for attr_match in re.finditer(attribute_pattern, provider_content):
            attr_name, attr_value = attr_match.groups()
            # Remove everything after and including '#'
            attr_value = attr_value.split('#')[0].strip()
            # Preserve quotes if they exist
            if attr_value.startswith('"') and attr_value.endswith('"'):
                provider_attributes[attr_name.strip()] = attr_value
            else:
                provider_attributes[attr_name.strip()] = attr_value.strip('"')
        providers[provider_name] = provider_attributes

    # Return the full file_path instead of os.path.basename(file_path)
    return file_path, variables, providers

def find_tf_files(directory):
    tf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.tf'):
                tf_files.append(os.path.join(root, file))
    return tf_files

def ensure_repo_exists(repo_url, local_path):
    if not os.path.exists(local_path):
        print(f"Repository not found locally. Cloning from {repo_url}...")
        try:
            subprocess.run(["git", "clone", repo_url, local_path], check=True)
            print("Repository cloned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            sys.exit(1)
    else:
        print("Repository already exists locally.")

def get_repo_relative_path(full_path, repo_path):
    return os.path.relpath(full_path, repo_path)

# GitHub repository URL and local path
github_repo_url = "https://github.com/Test-Org-0101/aws-terraform-1.git"
local_repo_path = './aws-terraform-1'  # Change this to your desired local path

# Ensure the repository exists locally
ensure_repo_exists(github_repo_url, local_repo_path)

# Update the terraform_directory to use the local repository path
terraform_directory = local_repo_path

# Extract repository name and owner from github_repo_url
repo_parts = github_repo_url.split('/')
repo_owner = repo_parts[-2]
repo_name = repo_parts[-1].replace('.git', '')

# Base GitHub URL
github_base_url = f"https://github.com/{repo_owner}/{repo_name}/blob/main/"

# Find all .tf files
tf_files = find_tf_files(terraform_directory)

# Prepare to store results
all_results = []

# Parse each .tf file
for file_path in tf_files:
    # Get the relative path of the file within the repository
    relative_path = get_repo_relative_path(file_path, terraform_directory)
    
    # Construct the full GitHub URL for this file
    file_github_url = github_base_url + relative_path.replace('\\', '/')
    
    # Combine repository name and relative path
    repo_and_path = f"{repo_name}\{relative_path}"
    
    full_file_path, parsed_variables, parsed_providers = parse_terraform_file(file_path)
    
    # Store results for variables
    for var_name, var_attributes in parsed_variables.items():
        for attr_name, attr_value in var_attributes.items():
            all_results.append([file_github_url, repo_and_path, 'variable', var_name, attr_name, attr_value])
    
    # Store results for providers
    for provider_name, provider_attributes in parsed_providers.items():
        for attr_name, attr_value in provider_attributes.items():
            all_results.append([file_github_url, repo_and_path, 'provider', provider_name, attr_name, attr_value])


# Write the results to a CSV file
output_file = 'terraform_parsed_results.csv'

with open(output_file, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Write header
    csvwriter.writerow(['GitHub URL', 'File Path', 'Type', 'Name', 'Attribute', 'Value'])
    
    # Write all results
    csvwriter.writerows(all_results)

print(f"Results have been written to {output_file}")