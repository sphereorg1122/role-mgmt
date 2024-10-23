import requests
import argparse
import time
import sys

def main():
    parser = argparse.ArgumentParser(description='Scan all repositories under a GitHub organization and search for specific values.')
    parser.add_argument('-o', '--organization', required=True, help='GitHub organization name')
    parser.add_argument('-v', '--values', required=True, nargs='+', help='Specific values to search for (enclose phrases in quotes)')
    parser.add_argument('-t', '--token', help='GitHub access token (required for private repos or higher rate limits)')
    
    args = parser.parse_args()

    org_name = args.organization
    specific_values = args.values
    access_token = args.token

    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if access_token:
        headers['Authorization'] = f'token {access_token}'

    # Fetch the list of repositories in the organization
    repos = []
    page = 1
    per_page = 100
    print(f"Fetching repositories for organization '{org_name}'...")
    while True:
        url = f'https://api.github.com/orgs/{org_name}/repos?per_page={per_page}&page={page}'
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f'Failed to fetch repositories: {response.text}')
            sys.exit(1)
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1

    print(f'Found {len(repos)} repositories.')

    matches = []

    # For each repository
    for repo in repos:
        repo_name = repo['name']
        full_repo_name = f"{org_name}/{repo_name}"
        print(f"\nSearching in repository {full_repo_name}...")
        for value in specific_values:
            print(f"  Searching for '{value}'...")
            # Build the search query
            query = f'"{value}" repo:{full_repo_name}'
            search_url = f"https://api.github.com/search/code"
            params = {'q': query, 'per_page': 100}
            total_count = None
            page = 1
            while True:
                params['page'] = page
                search_response = requests.get(search_url, headers=headers, params=params)
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    if total_count is None:
                        total_count = search_data.get('total_count', 0)
                        if total_count == 0:
                            print(f"    No matches found for '{value}' in {full_repo_name}.")
                            break
                        else:
                            print(f"    Found {total_count} matches for '{value}' in {full_repo_name}.")
                    for item in search_data.get('items', []):
                        matches.append({
                            'repo': full_repo_name,
                            'file': item['path'],
                            'value': value,
                            'html_url': item['html_url']
                        })
                    # Check if there are more pages
                    if 'next' in search_response.links:
                        page += 1
                        time.sleep(1)  # Sleep to respect rate limits
                    else:
                        break
                elif search_response.status_code == 403:
                    if 'Retry-After' in search_response.headers:
                        retry_after = int(search_response.headers['Retry-After'])
                        print(f"    Rate limit exceeded, retrying after {retry_after} seconds...")
                        time.sleep(retry_after)
                    else:
                        reset_time = int(search_response.headers.get('X-RateLimit-Reset', time.time() + 60))
                        wait_time = max(reset_time - int(time.time()), 1)
                        print(f"    Rate limit exceeded, retrying after {wait_time} seconds...")
                        time.sleep(wait_time)
                else:
                    print(f"    Failed to search code: {search_response.text}")
                    break

    # Report matches
    if matches:
        print('\nSearch complete. Matches found:')
        for match in matches:
            print(f"Repository: {match['repo']}, File: {match['file']}, Value: {match['value']}, URL: {match['html_url']}")
    else:
        print('\nSearch complete. No matches found.')

if __name__ == '__main__':
    main()
