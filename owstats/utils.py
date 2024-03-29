import os
from datetime import date, datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests

from owstats import CompStats, Player


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


def check_if_more_than_seven_days(d):
    now = datetime.now()                
    return (now - d).days > 7


def is_it_monday():
    return date.today().weekday() == 0 and datetime.now().hour < 3 # the first runs on Monday


def is_it_new_season(next_switch_date):
    if next_switch_date is None:
        return False
    now = datetime.now() 
    return next_switch_date < now


def make_plot(user, season=0):
    data = {'Games played': [],
        'Tank SR': [],
        'Damage SR': [],
        'Support SR': []
       }
    ranks = [1500, 2000, 2500, 3000, 3500, 4000]
    
    if season == 0:
        season = user.comp_stats[0].season

    for stat in user.comp_stats:
        if stat.season == season:
            data['Games played'].append(stat.games_played)
            data['Tank SR'].append(stat.rating_tank)
            data['Damage SR'].append(stat.rating_damage)
            data['Support SR'].append(stat.rating_support)
    
    # find min and max SR on chart
    allSR = data['Tank SR'] + data['Damage SR'] + data['Support SR']
    res = []
    for val in allSR:
        if val != None :
            res.append(val)

    df = pd.DataFrame(data,columns=['Games played','Tank SR','Damage SR','Support SR'])
    
    plt.plot(df['Games played'], df['Tank SR'], '.:b', label='Tank SR')
    plt.plot(df['Games played'], df['Damage SR'], '*:r', label='Damage SR')
    plt.plot(df['Games played'], df['Support SR'], '^:c', label='Support SR')
    plt.title(f'Season {season}: SR changes per role', loc = 'left')
    plt.xlabel('Games played')
    plt.ylabel('SR')
    plt.legend()
    plt.grid(axis = 'y')
    if res:
        minSR = min(res)
        maxSR = max(res)
        for rank in ranks:
            if rank + 50 > minSR and rank - 50 < maxSR:
                plt.axhline(y=rank, color='r', linestyle='-')
    # plt.show()
    plot_fn = f"{user.username}_{user.platform}_{user.region}_{season}.png"
    plot_dir = os.path.dirname(__loader__.path)
    plot_path = os.path.join(plot_dir, 'static/plots', plot_fn)
    plt.savefig(plot_path, dpi=100)
    plt.clf()


def get_player_seasons(username):
    seasons = []
    for season in CompStats.query.join(Player).filter_by(username=username).distinct(CompStats.season).order_by(CompStats.season.desc()):
        seasons.append(season.season)
    return seasons
