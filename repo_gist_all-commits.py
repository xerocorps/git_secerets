import getopt
import json
import os
import subprocess
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# Initialize token index for cycling
token_index = 0

def Usage():
    print("Usage: %s -u <github user/org> -d <directory> -r <repo> -n <number of commits> -l <listonly> -t <tokens>" % sys.argv[0])
    print("  -u <github user/org>  GitHub user or organization name")
    print("  -d <directory>        Local directory for repos and commits")
    print("  -r <repo>             Specific repo")
    print("  -n <number>           (optional) Number of commits (newest to oldest)")
    print("  -l <listonly>         (optional) List only, no checkout")
    print("  -t <tokens>           (optional) Comma-separated GitHub tokens")

def get_all_items_with_pagination(base_url, tokens):
    """Fetch all items from a paginated API."""
    global token_index
    items = []
    page = 1
    per_page = 100

    while True:
        url = f"{base_url}?per_page={per_page}&page={page}"
        try:
            headers = {'Authorization': f'token {tokens[token_index]}'}
            req = Request(url, headers=headers)
            f = urlopen(req)
            page_items = json.loads(f.read())
            if not page_items:
                break
            items.extend(page_items)
            page += 1
        except HTTPError as e:
            if e.code == 403:  # Rate limit exceeded
                print("Rate limit exceeded. Switching to the next token...")
                token_index = (token_index + 1) % len(tokens)
                continue
            elif e.code == 404:
                print(f"Warning: 404 Error when accessing {url}. No more data or invalid endpoint.")
                break
            else:
                raise e
    return items

def download_commits(user, repo, baseDirectory, numberCommits, listOnly, tokens):
    commitsLink = f"https://api.github.com/repos/{user}/{repo}/commits"
    commits = get_all_items_with_pagination(commitsLink, tokens)
    print(f"repo: '{repo}' ; total commits: {len(commits)}")

    repoLink = f"https://github.com/{user}/{repo}.git"
    repoURL = f"https://github.com/{user}/{repo}"
    print(f"Repository URL: {repoURL}")  # Print repo URL once

    count = 0
    repoDirectory = os.path.join(baseDirectory, 'repos', repo)
    os.makedirs(repoDirectory, exist_ok=True)

    for commit in commits:
        sha = commit['sha']
        commitURL = f"https://github.com/{user}/{repo}/tree/{sha}"  # Updated commit URL
        print(f"Commit URL: {commitURL}")

        if not listOnly:
            subdir = f"{repo}-{sha}"
            commitDirectory = os.path.join(repoDirectory, subdir)
            subprocess.call(['git', 'clone', repoLink, commitDirectory])
            subprocess.call(['git', '-C', commitDirectory, 'checkout', sha])

        count += 1
        if count >= numberCommits:
            break

def process_user_repos_and_gists(user, baseDestDirectory, numberCommits, listOnly, tokens):
    reposLink = f"https://api.github.com/users/{user}/repos"
    repos = get_all_items_with_pagination(reposLink, tokens)
    print(f"Total repos for {user}: {len(repos)}")

    for repo in repos:
        repoName = repo['name']
        download_commits(user, repoName, baseDestDirectory, numberCommits, listOnly, tokens)

    gistsLink = f"https://api.github.com/users/{user}/gists"
    gists = get_all_items_with_pagination(gistsLink, tokens)
    print(f"Total gists for {user}: {len(gists)}")

    gistDirectory = os.path.join(baseDestDirectory, 'gists')
    for gist in gists:
        gistURL = gist['html_url']
        print(f"Gist URL: {gistURL}")
        if not listOnly:
            subdir = os.path.join(gistDirectory, gist['id'])
            subprocess.call(['git', 'clone', gist['git_pull_url'], subdir])

def main():
    global tokens
    githubUser = ''
    destDirectory = ''
    currentRepo = ''
    numberCommits = 10000000
    listOnly = False
    tokens = []

    try:
        ouropts, args = getopt.getopt(sys.argv[1:], "u:d:r:n:lt:h")
        for o, a in ouropts:
            if o == '-u':
                githubUser = a
            elif o == '-d':
                destDirectory = a
            elif o == '-r':
                currentRepo = a
            elif o == '-n':
                numberCommits = int(a)
            elif o == '-l':
                listOnly = True
            elif o == '-t':
                tokens = a.split(',')
            elif o == '-h':
                Usage()
                sys.exit(0)
    except getopt.GetoptError as e:
        print(str(e))
        Usage()
        sys.exit(2)

    if not githubUser or not destDirectory or not tokens:
        print("Please provide a GitHub user, destination directory, and tokens.")
        Usage()
        sys.exit(0)

    baseDestDirectory = os.path.join(destDirectory, githubUser)
    os.makedirs(baseDestDirectory, exist_ok=True)

    # Process the main user/organization
    process_user_repos_and_gists(githubUser, baseDestDirectory, numberCommits, listOnly, tokens)

    # If it's an organization, fetch and process members
    orgMembersLink = f"https://api.github.com/orgs/{githubUser}/members"
    members = get_all_items_with_pagination(orgMembersLink, tokens)
    if members:
        print(f"Organization '{githubUser}' has {len(members)} members.")
        for member in members:
            memberLogin = member['login']
            print(f"Processing member: {memberLogin}")
            memberDirectory = os.path.join(baseDestDirectory, 'members', memberLogin)
            os.makedirs(memberDirectory, exist_ok=True)
            process_user_repos_and_gists(memberLogin, memberDirectory, numberCommits, listOnly, tokens)

if __name__ == "__main__":
    main()
