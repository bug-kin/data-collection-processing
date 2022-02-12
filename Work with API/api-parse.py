import json

import requests


def write_into_file(user, repository_list):
    with open(f'{user}.json', 'w') as data:
        json.dump(repository_list, data, indent=4)
    return 0


def get_repos_list(user):
    rp_list = []
    url = f'https://api.github.com/users/{user}/repos'
    response = requests.get(url)
    if response.ok:
        repositories = json.loads(response.text)
        for repository in repositories:
            rp_list.append(repository["name"])
    else:
        print("User not found...")
    return {user: rp_list}


if __name__ == "__main__":
    username = input("Please write github username: ")
    write_into_file(username, get_repos_list(username))
