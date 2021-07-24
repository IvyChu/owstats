import requests


BASE_URL = 'https://ow-api.com/v1/stats'

def get_api_response(platform, region, username):
    url = f'{BASE_URL}/{platform}/{region}/{username}/profile'

    response = requests.get(url,
                        headers={
                            "Host": "ow-api.com",
                            "User-Agent": "PythonTest 0.2",
                            "DNT": "1",
                            "Connection": "keep-alive",
                            "Cookie": "__cfduid=df6937f525b58b9a98ac7d59a94d2c4761590714472",
                            "Upgrade-Insecure-Requests": '1',
                            "Cache-Control": "max-age=0",
                            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                        }
                        )

    return response