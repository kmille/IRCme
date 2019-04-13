import requests


def go():
    headers= { 'User-Agent': 'Feuerfuchs' }
    req = requests.get("https://ctftime.org/event/686/tasks/", headers=headers) 
    if "hoster" in req.text:
        return "yea write up ist da"
    else:
        return []
