import os
import requests
import csv
import datetime

def get_java_build_tool(file):
    if file['name'].endswith('pom.xml'):
        return 'maven'
    elif file['name'].endswith('build.gradle'):
        return 'gradle'

def get_javascript_build_tool(file):
    if file['name'].endswith('package.json'):
        return 'npm'
    elif file['name'].endswith('yarn.lock'):
        return 'yarn'

def get_build_tool_helper(file, language):
    match language:
        case 'java':
            return get_java_build_tool(file)
        case 'javascript':
            return get_javascript_build_tool(file)
        case _:
            return None

def get_build_tool(repo, language):
    build_file = None
    response = requests.get(api_url + repo + '/contents', headers={'Authorization': access_token})
    for item in response.json():
        if build_file is not None:
            return build_file
        if item['type'] == 'file':
            build_file = get_build_tool_helper(item, language)
        elif item['type'] == 'dir':
            folder = requests.get(item['url'], headers={'Authorization': access_token})
            for file in folder.json():
                if isinstance(file, dict):
                    build_file = get_build_tool_helper(file, language)
                    if build_file is not None:
                        return build_file
    return build_file

def print_statements_to_file(repo, language, api_language, branch_count, repo_size, branch_names, build_tool):
    print(f'\nFor "{api_url + repo}" the language with max size is {language}')
    print(f'and the major language returned by the GitHub API is {api_language}')
    print(f'and the branch count is: {branch_count}')
    print(f'and the repo size in KB is: {repo_size}')
    print(f'Branch names: {branch_names}')

    with open(logs, 'a') as file:
        file.write(f'\nFor "{api_url + repo}" the language with max size is {language}\n')
        file.write(f'and the major language returned by the GitHub API is {api_language}\n')
        file.write(f'and the branch count is: {branch_count}\n')
        file.write(f'and the repo size in KB is: {repo_size}\n')
        file.write(f'Branch names: {branch_names}\n')
        if language.lower() in ['java', 'javascript']:
            print(f'and the {language} build tool is {build_tool}')
            file.write(f'and the {language} build tool is {build_tool}\n')

    with open(summary, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([repo, repo_size, branch_count, language, branch_names])

    return

def get_repo_info(repo):
    # find major language
    response = requests.get(api_url + repo + '/languages', headers={'Authorization': access_token})
    
    languages_data = response.json()
    if isinstance(languages_data, dict):
        language = max(languages_data, key=languages_data.get)
    else:
        print(f"Unexpected format for languages data in repo: {repo}")
        return
    
    response = requests.get(api_url + repo, headers={'Authorization': access_token})
    repo_data = response.json()

    # Check if the response is a dictionary (valid) and get the repo size
    if isinstance(repo_data, dict):
        api_language = repo_data.get('language')
        repo_size = repo_data.get('size')
    else:
        print(f"Unexpected format for repo data in repo: {repo}")
        return
    
    # find branch count
    response = requests.get(api_url + repo + '/branches', headers={'Authorization': access_token})
    branches_data = response.json()

    if isinstance(branches_data, list):
        branch_count = len(branches_data)
        branch_names = [branch['name'] for branch in branches_data]
    else:
        print(f"Unexpected format for branches data in repo: {repo}")
        return

    # find build tool
    build_tool = None
    if language.lower() == 'java' or language.lower() == 'javascript':
        build_tool = get_build_tool(repo, language.lower())
    
    print_statements_to_file(repo, language, api_language, branch_count, repo_size, branch_names, build_tool)
    return


def main():
    global file, csv_file, logs, summary, api_url, api_org_url, access_token, org
    api_url = "https://api.github.com/repos/"
    access_token = os.getenv('GITHUB_TOKEN')
    org = "arunbattepati"
    logs = "logs.txt"
    summary = "pre-summary.csv"

    with open(summary, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Repo', 'Repo Size (KB)', 'Branch Count', 'Language', 'Branch Names'])
    
    ct_start = datetime.datetime.now()
    print(f'\nStart time {ct_start}\n')
    with open(logs, 'a') as file:
        file.write(f'\nStart time {ct_start}\n\n')

    with open('repos.txt', mode='r') as file:
        for line in file:
            repo = line.strip()  # Use line.strip() to get owner/repo format
            get_repo_info(repo)

    ct_end = datetime.datetime.now()
    print(f'\nEnd time {ct_end}')
    print(f'Total time taken {ct_end - ct_start}')
    with open(logs, 'a') as file:
        file.write(f'\nEnd time {ct_end}\n')
        file.write(f'Total time taken {ct_end - ct_start}\n\n')

if __name__ == '__main__':
    main()
