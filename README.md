# migration_utilities

`migration_utilities` is a set of Python scripts that automate the migration of GitHub repositories from a source organization to a target organization. The process includes gathering pre-migration data, performing the migration, and generating post-migration comparisons between the source and target repositories.

## Table of Contents

- [Overview](#overview)
- [Pre-migration Script](#pre-migration-script)
- [Migration Script](#migration-script)
- [Post-migration Script](#post-migration-script)
- [Example CSV Files](#example-csv-files)
- [Requirements](#requirements)
- [Environment Setup](#environment-setup)
- [Conclusion](#conclusion)

---

## Overview

The migration process consists of three stages:

1. **Pre-migration**: Gather detailed information about the source repositories before migration, such as primary language, branch count, repository size, and build system.
   
2. **Migration**: Automatically migrate repositories from a source organization to a target organization. During migration, the repositories are cloned, updated, and pushed to the target organization. Additionally, CI workflow files can be added as part of the migration process.
   
3. **Post-migration**: After migration, the source and target repositories are compared to ensure that the migration was successful. This includes comparing details like branch count, repository size, build system, and branch names.

---

## Pre-migration Script

### Description:
The pre-migration script (`pre_migration.py`) gathers pre-migration details for each repository in the `source_repos.csv` file and stores the results in `pre_migration_summary.csv`.

### Pre-migration Data Collected:
- Repository Name
- Primary Language
- Branch Count
- Repository Size (KB)
- Branch Names
- Build System (detected from common build files)

### How to Use:
1. Ensure you have a `source_repos.csv` file with the list of source repositories (format: `org/repo`).
2. Set your GitHub token as an environment variable:
   ```bash
   export GITHUB_TOKEN=<your-github-token>
3. Run the pre_migration.py script
   ```bash
   python pre_migration.py
4. The script will generate pre_migration_summary.csv with the details of each source repository.
---

## Migration Script
### Description:
The migration script (migration.py) automates the migration of repositories from the source organization to the target organization. It creates or updates repositories in the target organization, clones the repositories, pushes them to the target, and optionally adds CI workflow files.

### Migration Process:
- Clones the source repositories.
- Adds CI workflow files (optional).
- Pushes the repositories to the target organization.
- Logs the details of each migration in migration_summary.csv and generates target_repos.csv containing the list of migrated repositories in org/repo format.
### How to Use:
1. Prepare your source_repos.csv file with the list of source repositories (format: org/repo).
2. Set your GitHub token as an environment variable:
   ```bash
   export GITHUB_TOKEN=<your-github-token>
3. Run the migration.py script:
   ```bash
   python migration.py
4. The script will generate two files:
migration_summary.csv: Details of each migrated repository.
target_repos.csv: A list of the migrated repositories in the target organization.
Files Generated:
migration_summary.csv: Contains the details of the migration for each source repository, including the target repository URL.
target_repos.csv: Contains the target repository names in the format org/repo.
Post-migration Script
Description:
The post-migration script (post_migration.py) compares the source and target repositories after the migration process. It gathers details about the target repositories and compares them with the source repositories to ensure that the migration was successful.

Post-migration Data Collected:
Source and Target Repository Name
Primary Language (source and target)
Branch Count (source and target)
Repository Size (KB)
Branch Names (source and target)
Build System (source and target)
Status (whether the branch count and size match between source and target)
How to Use:
Ensure you have the following CSV files:

source_repos.csv: List of source repositories.
target_repos.csv: List of target repositories (generated during the migration step).
Set your GitHub token as an environment variable:

bash
Copy code
export GITHUB_TOKEN=<your-github-token>
Run the post_migration.py script:

bash
Copy code
python post_migration.py
The script will generate post_migration_summary.csv containing a comparison of the source and target repositories.

Files Generated:
post_migration_summary.csv: Contains a comparison of the source and target repositories, including details such as branch count, repository size, branch names, build system, and a status indicating if the migration was successful (Match or Mismatch).
## Example CSV Files
source_repos.csv:
bash
Copy code
arunbattepati/java-app
arunbattepati/npm-app
senseops/python_app
target_repos.csv (Generated during migration):
bash
Copy code
capgemini-cg-demo/java-app
capgemini-cg-demo/npm-app
capgemini-cg-demo/python_app
post_migration_summary.csv (Generated after post-migration):
source_repo	target_repo	source_primary_language	target_primary_language	source_branch_count	target_branch_count	source_repo_size	target_repo_size	source_branches	target_branches	source_build_system	target_build_system	status
arunbattepati/java-app	capgemini-cg-demo/java-app	Java	Java	2	2	150	150	master, develop	master, develop	maven	maven	Match
arunbattepati/npm-app	capgemini-cg-demo/npm-app	JavaScript	JavaScript	3	3	75	70	master, feature-1, fix	master, feature-1, fix	npm	npm	Mismatch
Requirements
Python: Version 3.x
GitHub Token: Ensure you generate a GitHub Personal Access Token with appropriate repository permissions.
Python Libraries:
Install the required libraries using pip:

bash
Copy code
pip install PyGithub
Environment Setup
Set GitHub Token:
You need to set your GitHub token as an environment variable:

Linux/Mac:

bash
Copy code
export GITHUB_TOKEN=<your-github-token>
Windows:

bash
Copy code
set GITHUB_TOKEN=<your-github-token>
Conclusion
This set of scripts provides a complete automation process for migrating repositories between organizations on GitHub. It handles the pre-migration, migration, and post-migration processes efficiently while generating detailed reports on each step to ensure successful migrations.
