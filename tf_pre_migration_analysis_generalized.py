import re
import csv
import os
import subprocess
import sys

def parse_terraform_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Pattern for blocks with one or two quoted values
    block_pattern = r'(\w+)\s+"([^"]+)"(?:\s+"([^"]+)")?\s*{([^}]*)}'
    attribute_pattern = r'(\w+)\s*=\s*(.+)'

    blocks = {}

    for match in re.finditer(block_pattern, content, re.DOTALL):
        block_type, block_name1, block_name2, block_content = match.groups()
        block_attributes = {}
        for attr_match in re.finditer(attribute_pattern, block_content):
            attr_name, attr_value = attr_match.groups()
            # Remove everything after and including '#'
            attr_value = attr_value.split('#')[0].strip()
            # Preserve quotes if they exist
            if attr_value.startswith('"') and attr_value.endswith('"'):
                block_attributes[attr_name.strip()] = attr_value
            else:
                block_attributes[attr_name.strip()] = attr_value.strip('"')
        
        # Determine the block name based on whether it has one or two quoted values
        if block_name2:
            combined_name = f"{block_name1}/{block_name2}"
        else:
            combined_name = block_name1

        if block_type not in blocks:
            blocks[block_type] = {}
        blocks[block_type][combined_name] = block_attributes

    return file_path, blocks

def parse_tfvars_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    tfvars_pattern = r'(\w+)\s*=\s*(.+)'
    tfvars = {}

    for match in re.finditer(tfvars_pattern, content):
        var_name, var_value = match.groups()
        # Remove everything after and including '#'
        var_value = var_value.split('#')[0].strip()
        # Preserve quotes if they exist
        if var_value.startswith('"') and var_value.endswith('"'):
            tfvars[var_name.strip()] = var_value
        else:
            tfvars[var_name.strip()] = var_value.strip('"')

    return file_path, tfvars

def find_tf_and_tfvars_files(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for file in filenames:
            if file.endswith('.tf') or file.endswith('.tfvars'):
                files.append(os.path.join(root, file))
    return files

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

# Find all .tf and .tfvars files
all_files = find_tf_and_tfvars_files(terraform_directory)

# Prepare to store results
all_results = []

# Parse each file
for file_path in all_files:
    # Get the relative path of the file within the repository
    relative_path = get_repo_relative_path(file_path, terraform_directory)
    
    # Construct the full GitHub URL for this file
    file_github_url = github_base_url + relative_path.replace('\\', '/')
    
    # Combine repository name and relative path
    repo_and_path = f"{repo_name}\{relative_path}"
    
    if file_path.endswith('.tf'):
        full_file_path, parsed_blocks = parse_terraform_file(file_path)
        
        # Store results for all block types
        for block_type, blocks in parsed_blocks.items():
            for block_name, block_attributes in blocks.items():
                for attr_name, attr_value in block_attributes.items():
                    all_results.append([file_github_url, repo_and_path, block_type, block_name, attr_name, attr_value])
    
    elif file_path.endswith('.tfvars'):
        full_file_path, parsed_tfvars = parse_tfvars_file(file_path)
        
        # Store results for tfvars
        for var_name, var_value in parsed_tfvars.items():
            all_results.append([file_github_url, repo_and_path, 'tfvars', var_name, 'value', var_value])

# Write the results to a CSV file
output_file = 'terraform_parsed_results_generalized_1.csv'

with open(output_file, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Write header
    csvwriter.writerow(['GitHub URL', 'File Path', 'Type', 'Name', 'Attribute', 'Value'])
    
    # Write all results
    csvwriter.writerows(all_results)

print(f"Results have been written to {output_file}")