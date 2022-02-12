import json
import os

import requests


def get_request(url, token):
    response = requests.get(url, headers={'Authorization': f'token {token}'})
    if response.ok:
        ok_answer = json.loads(response.text)
        return ok_answer
    elif response.status_code == 401:
        error_answer = {"Error message": f"{response.status_code} {response.reason}"}
        return error_answer


def write_in_file(data):
    with open(f'data.json', 'w') as about_account:
        json.dump(data, about_account, indent=5)
    return 0


if __name__ == '__main__':
    URL = "https://api.github.com/user"
    TOKEN = os.environ.get('TOKEN')
    answer = get_request(URL, TOKEN)
    write_in_file(answer)
