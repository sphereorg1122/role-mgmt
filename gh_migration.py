import requests

# Replace these variables with your own values
GITHUB_TOKEN = os.getenv('MIGKEY')
ORG_NAME = 'your_organization_name'
REPO_NAME = 'your_repository_name'
TEAM_NAME = 'your_team_name'
ROLE = 'maintain'  # Possible values: 'pull', 'push', 'maintain', 'admin'

def add_team_to_repo(org, repo, team, role, token):
    url = f'https://api.github.com/orgs/{org}/teams/{team}/repos/{org}/{repo}'
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
