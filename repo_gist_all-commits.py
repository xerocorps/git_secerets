import getopt
import json
import os
import subprocess
import sys
from urllib.request import urlopen
from urllib.error import HTTPError

def Usage():
    print("Usage: %s -u <github user> -d <directory> -r <repo> -n <number of commits> -l <listonly>" % sys.argv[0])
    print("  -u <github user>  github user/org name")
    print("  -d <directory>    local directory for repos and commits")
    print("  -r <repo>         specific repo")
    print("  -n <number>       (optional) number of commits (newest to oldest)")
    print("  -l <listonly>     (optional) list only, no checkout")

def get_all_items(url):
    items = []
    try:
        f = urlopen(url)
        items = json.loads(f.read())
    except HTTPError as e:
        if e.code == 404:
            print(f"Warning: 404 Error when accessing {url}. No more data or invalid endpoint.")
        else:
            raise e
    return items

def download_commits(githubUser, repo, baseDirectory, numberCommits, listOnly):
    commitsLink = f"https://api.github.com/repos/{githubUser}/{repo}/commits"
    f = urlopen(commitsLink)
    commits = json.loads(f.readline())
    print(f"repo: '{repo}' ; total commits: {len(commits)}")

    repoLink = f"https://github.com/{githubUser}/{repo}.git"
    count = 0
    repoDirectory = os.path.join(baseDirectory, 'repos', repo)
    os.makedirs(repoDirectory, exist_ok=True)

    for commit in commits:
        d = commit['commit']['committer']['date']
        name = commit['commit']['committer']['name']
        sha = commit['sha']
        subdir = f"{repo}-{d}-{name}-{sha}"
        commitDirectory = os.path.join(repoDirectory, subdir)
        print(subdir)
        if not listOnly:
            # Clone the repository into the specific subdirectory
            subprocess.call(['git', 'clone', repoLink, commitDirectory])
            # Check out the specific commit
            subprocess.call(['git', '-C', commitDirectory, 'checkout', sha])

        count += 1
        if count >= numberCommits:
            break

def main():
    githubUser  = ''
    destDirectory = ''
    currentRepo = ''
    numberCommits = 10000000
    listOnly = False
    try:
        # process command arguments
        ouropts, args = getopt.getopt(sys.argv[1:],"u:d:r:n:lh")
        for o, a in ouropts:
            if   o == '-u':
                githubUser = a
            if   o == '-d':
                destDirectory = a
            if   o == '-r':
                currentRepo = a
            if   o == '-n':
                numberCommits = int(a)
            if   o == '-l':
                listOnly = True
            elif o == '-h':
                Usage()
                sys.exit(0)
    except getopt.GetoptError as e:
        print(str(e))
        Usage()
        sys.exit(2)

    if type(githubUser) != str or len(githubUser) <= 0:
        print("please use -u for github user")
        Usage()
        sys.exit(0)
    if type(destDirectory) != str or len(destDirectory) <= 0:
        print("please use -d for local directory")
        Usage()
        sys.exit(0)

    # Ensure the base directory exists
    baseDestDirectory = os.path.join(destDirectory, githubUser)
    os.makedirs(baseDestDirectory, exist_ok=True)

    # Get all repositories (with pagination)
    reposLink = f"https://api.github.com/users/{githubUser}/repos?type=all&per_page=100"
    repos = get_all_items(reposLink)
    print(f"total repos: {len(repos)}")

    # If a specific repository is provided, filter for it
    if currentRepo:
        repos = [repo for repo in repos if repo['name'] == currentRepo]
        if not repos:
            print(f"Repository '{currentRepo}' not found.")
            sys.exit(0)

    # Ensure separate directories for repos and gists exist
    os.makedirs(os.path.join(baseDestDirectory, 'repos'), exist_ok=True)
    os.makedirs(os.path.join(baseDestDirectory, 'gists'), exist_ok=True)

    # Download commits for each repository
    for repo in repos:
        repoName = repo['name']
        print(f"Processing repository: {repoName}")
        download_commits(githubUser, repoName, baseDestDirectory, numberCommits, listOnly)

    # Get and download gists
    gistsLink = f"https://api.github.com/users/{githubUser}/gists"
    gists = get_all_items(gistsLink)
    print(f"total gists: {len(gists)}")

    gistDirectory = os.path.join(baseDestDirectory, 'gists')
    for gist in gists:
        subdir = os.path.join(gistDirectory, gist['id'])
        print(f"Processing gist: {gist['id']}")
        if not listOnly:
            subprocess.call(['git', 'clone', gist['git_pull_url'], subdir])

if __name__ == "__main__":
    main()
