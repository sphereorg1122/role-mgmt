import requests
import os
# Replace these variables with your own values
GITHUB_TOKEN = os.getenv('MIGKEY')
ORG_NAME = 'sphere1122'
REPO_NAME = 'role-mgmt'
TEAM_NAME = 'sphere-team'
ROLE = 'maintain'  # Possible values: 'pull', 'push', 'maintain', 'admin'

def add_team_to_repo(org, repo, team, role, token):
    url = f'https://api.github.com/orgs/sphere1122/teams/sphere-team/repos/sphere1122/role-mgmt'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'permission': role
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 204:
        print(f'Successfully added {team} to {repo} with {role} role.')
    else:
        print(f'Failed to add team to repo: {response.status_code} - {response.text}')

if __name__ == '__main__':
    add_team_to_repo(ORG_NAME, REPO_NAME, TEAM_NAME, ROLE, GITHUB_TOKEN)
