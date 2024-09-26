import os
# from dotenv import find_dotenv, load_dotenv # type: ignore
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
        if build_file != None:
            return build_file
        if item['type'] == 'file':
            build_file = get_build_tool_helper(item, language)
        elif item['type'] == 'dir':
            folder = requests.get(item['url'], headers={'Authorization': access_token})
            for file in folder.json():
                if type(file) == dict:
                    build_file = get_build_tool_helper(file, language)
                    if build_file != None:
                        return build_file

    return build_file

def print_statements_to_file(repo, language, api_language, branch_count, repo_size, branch_names, build_tool):
    
    print('\nFor "' + api_url + repo + '" the language with max size is ' + language)
    print('and the major language returned by the GitHub API is ' + api_language)
    print('and the branch count is: ' + str(branch_count))
    print('and the repo size in KB is: ' + str(repo_size))
    print('Branch names: ' + str(branch_names))
    # print('The team names and their permissions are: '+ str(team_names_and_permissions))

    file = open(logs, 'a')
    file.write('\nFor "' + api_url + repo + '" the language with max size is ' + language + '\n')
    file.write('and the major language returned by the GitHub API is ' + api_language + '\n')
    file.write('and the branch count is: ' + str(branch_count) + '\n')
    file.write('and the repo size in KB is: ' + str(repo_size) + '\n')
    file.write('Branch names: ' + str(branch_names) + '\n')
    # file.write('The team names and their permissions are: '+ str(team_names_and_permissions) + '\n')
    if language.lower() == 'java' or language.lower() == 'javascript':
        print('and the ' + language + ' build tool is ' + str(build_tool))
        file.write('and the ' + language + ' build tool is ' + str(build_tool) + '\n')
    file.close()

    csv_file = open(summary, 'a', newline='')
    writer = csv.writer(csv_file)
    # writer.writerow([repo, repo_size, branch_count, language, branch_names, team_names_and_permissions])
    writer.writerow([repo, repo_size, branch_count, language, branch_names])

    csv_file.close()

    return

def get_repo_info(repo):
    
    # find major language
    response = requests.get(api_url + repo + '/languages', headers={'Authorization': access_token})
    language = max(response.json(), key = response.json().get)
    response = requests.get(api_url + repo, headers={'Authorization': access_token})
    api_language = response.json().get('language')
    
    # find branch count
    response = requests.get(api_url + repo + '/branches', headers={'Authorization': access_token})
    branch_count = len(response.json())
    
    # find repo size
    response = requests.get(api_url + repo, headers={'Authorization': access_token})
    repo_size = response.json().get('size')

    # find branch names
    response = requests.get(api_url + repo + '/branches', headers={'Authorization': access_token})
    branch_names = [branch['name'] for branch in response.json()]

    # find team permissions for the repo
    # response = requests.get(api_url + repo + '/teams', headers={'Authorization': access_token})
    # team_names_and_permissions = [(team['name'], team['permission']) for team in response.json()]

    # find build tool
    build_tool = None
    if language.lower() == 'java' or language.lower() == 'javascript':
        build_tool = get_build_tool(repo, language.lower())
    
    # print_statements_to_file(repo, language, api_language, branch_count, repo_size, branch_names, team_names_and_permissions, build_tool)
    print_statements_to_file(repo, language, api_language, branch_count, repo_size, branch_names, build_tool)

    return
    
def get_org_info(org):
    
    # find team count, names, and permissions
    response = requests.get(api_org_url + org + '/teams', headers={'Authorization': access_token})
    team_count = len(response.json())
    print('For org "' + org + '" the team count is ' + str(team_count))
    print('The team names are: ' + str([team['name'] for team in response.json()]))
    file = open(logs, 'a')
    file.write('For org "' + org + '" the team count is ' + str(team_count) + '\n')
    file.write('The team names are' + str([team['name'] for team in response.json()]) + '\n')
    file.close()

    return

def main():
    # dotenv_path = find_dotenv()
    # load_dotenv(dotenv_path)
    global file, csv_file, logs, summary, api_url, api_org_url, access_token, org
    api_url = "https://api.github.com/repos/"
    api_org_url = "https://api.github.com/users/"
    access_token = os.getenv('GITHUB_TOKEN')
    org = "arunbattepati"
    logs = "logs.txt"
    summary = "pre-summary.csv"

    csv_file = open(summary, 'w', newline='')
    writer = csv.writer(csv_file)
    writer.writerow(['Repo', 'Repo Size (KB)', 'Branch Count', 'Language', 'Branch Names', 'Team Names and Permissions'])
    csv_file.close()

    ct_start = datetime.datetime.now()
    print('\nStart time ' + str(ct_start) + '\n')
    file = open(logs, 'a')
    file.write('\nStart time ' + str(ct_start) + '\n\n')
    file.close()

    # get_org_info(org)

    with open('repos.csv', mode='r') as file:
        heading = next(file)
        csvFile = csv.reader(file)
        for line in csvFile:
            repo = line[0].split('.com/')[1]
            get_repo_info(repo)

    ct_end = datetime.datetime.now()
    print('\nEnd time ' + str(ct_end))
    print('Total time taken ' + str(ct_end - ct_start))
    file = open(logs, 'a')
    file.write('\nEnd time ' + str(ct_end) + '\n')
    file.write('Total time taken ' + str(ct_end - ct_start) + '\n\n')
    file.close()

    return

if __name__ == '__main__':
    main()