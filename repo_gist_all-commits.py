#!/usr/bin/python

# python3 ./all-github.py -u <user> -d <directory>
#
# Tool to inspect Github and pull local copies of all repos and gists
# for the given user.
#
# Why?  Every ask yourself the question 'I know I did this before, but
#       which repos was it in?'
# With all files local, you can use any serach-in-files app to look.
#
# Companion App: all-git-commits.py pull commits for a repo.

import getopt
import json
import os
import shutil
import subprocess
import sys
from urllib.request import urlopen

def Usage():
  print("Usage: %s -u <github user> -d <directory>" % sys.argv[0])
  print("  -u <github user>  github user name")
  print("  -d <directory>    local directory for repos and gists")

def main():

  githubUser  = ''
  destDirectory = ''
  try:
    # process command arguments
    ouropts, args = getopt.getopt(sys.argv[1:],"u:d:h")
    for o, a in ouropts:
      if   o == '-u':
        githubUser = a
      if   o == '-d':
        destDirectory = a
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


  reposLink = "https://api.github.com/users/{0}/repos?type=all&per_page=100&page=1".format(githubUser)
  f = urlopen(reposLink)
  repos = json.loads(f.readline())
  print("total repos: {0}".format(len(repos)))

  gistsLink = "https://api.github.com/users/{0}/gists".format(githubUser)
  f = urlopen(gistsLink)
  gists = json.loads(f.readline())
  print("total gists: {0}".format(len(gists)))

  os.mkdir(destDirectory)
  os.mkdir(os.path.join(destDirectory, 'repos'))
  os.mkdir(os.path.join(destDirectory, 'gists'))

  print('cd repos')
  os.chdir(os.path.join('.', destDirectory, 'repos'))
  with open('repos.json', 'w') as outfile:
    json.dump(repos, outfile, indent=2)
  for repo in repos:
    print(repo['html_url'])
    subprocess.call(['git', 'clone', repo['html_url']])
    print()
  print('cd ..')
  os.chdir(os.path.join('..', '..'))

  print('cd gists')
  os.chdir(os.path.join('.', destDirectory, 'gists'))
  with open('gists.json', 'w') as outfile:
    json.dump(gists, outfile, indent=2)
  for gist in gists:
    print(gist['git_pull_url'])
    subprocess.call(['git', 'clone', gist['git_pull_url']])
    print()
  print('cd ..')
  os.chdir(os.path.join('..', '..'))


if __name__ == "__main__":
  main()
@xerocorps
Comment
