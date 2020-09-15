import csv
import datetime
import logging
import os.path
import time
from socket import gaierror

import pandas
import requests
import urllib3

logging.basicConfig(filename=f'OWstats-{datetime.datetime.now().strftime("%Y-%m")}.log',
                    level=logging.INFO,
                    format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %X'
                    )
username = os.environ.get('OW_USERNAME')
platform = 'psn'


class OWstats:
    url = f'https://owapi.net/api/v3/u/{username}/stats?platform={platform}'
    stats_csv_file = 'OWstats.csv'
    sleep_time = 60 * 5  # number of minutes to wait until the next run
    sleep_time_extended = False

    def increase_sleep_time(self):
        self.sleep_time = self.sleep_time + 60 * 15
        self.sleep_time_extended = True

    def reset_sleep_time(self):
        self.sleep_time = 60 * 5

    def get_stats_from_api(self):
        logging.info("Started API call")
        logging.info(f'url: {self.url}')
        try:

            response = requests.get(self.url,
                                    headers={
                                        "Host": "owapi.net",
                                        "User-Agent": "PythonTest 0.2",
                                        "DNT": "1",
                                        "Connection": "keep-alive",
                                        "Cookie": "__cfduid=df6937f525b58b9a98ac7d59a94d2c4761590714472",
                                        "Upgrade-Insecure-Requests": '1',
                                        "Cache-Control": "max-age=0"
                                    }
                                    )
        except urllib3.exceptions.MaxRetryError:
            logging.exception("MaxRetryError - Connection problems, let's wait for a while...")
            self.increase_sleep_time()
            return
        except gaierror:
            logging.exception("gaierror - Connection problems, let's wait for a while...")
            self.increase_sleep_time()
            return

        # Check the response
        if response:
            logging.info('Request is successful.')

            try:
                # Get JSON from the response
                r_json = response.json()
                games = support_comprank = r_json['any']['stats']['competitive']['overall_stats']['games']
                support_tier = r_json['any']['stats']['competitive']['overall_stats']['support_tier']
                support_comprank = r_json['any']['stats']['competitive']['overall_stats']['support_comprank']
                all_damage_done = r_json['any']['stats']['competitive']['game_stats']['all_damage_done']
                barrier_damage_done = r_json['any']['stats']['competitive']['game_stats']['barrier_damage_done']
                damage_done = r_json['any']['stats']['competitive']['game_stats']['damage_done']
                deaths = r_json['any']['stats']['competitive']['game_stats']['deaths']
                eliminations = r_json['any']['stats']['competitive']['game_stats']['eliminations']
                final_blows = r_json['any']['stats']['competitive']['game_stats']['final_blows']
                objective_kills = r_json['any']['stats']['competitive']['game_stats']['objective_kills']
                objective_time = r_json['any']['stats']['competitive']['game_stats']['objective_time']
                time_spent_on_fire = r_json['any']['stats']['competitive']['game_stats']['time_spent_on_fire']
                games_lost = r_json['any']['stats']['competitive']['game_stats'].get('games_lost', 0)
                games_played = r_json['any']['stats']['competitive']['game_stats'].get('games_played', 0)
                games_tied = r_json['any']['stats']['competitive']['game_stats'].get('games_tied', 0)
                # games_tied = r_json['any']['stats']['competitive']['game_stats']['games_tied']
                games_won = r_json['any']['stats']['competitive']['game_stats'].get('games_won', 0)
                time_played = r_json['any']['stats']['competitive']['game_stats'].get('time_played', 0)
                defensive_assists = r_json['any']['stats']['competitive']['game_stats']['defensive_assists']
                healing_done = r_json['any']['stats']['competitive']['game_stats']['healing_done']
                offensive_assists = r_json['any']['stats']['competitive']['game_stats']['offensive_assists']
            except KeyError:
                print('\n\nKeyError - API mapping issue?')
                # logging.error('KeyError - API mapping issue?')
                logging.exception('KeyError - API mapping issue?')
                return

            ts = time.time()
            ds = datetime.datetime.now().strftime("%Y-%m-%d %X")
            do_we_write = False

            # Did we already start this file?
            if os.path.isfile(self.stats_csv_file):
                # Read the file to check if the number of games has changed, so we only log changes in SR
                csv_file = pandas.read_csv(self.stats_csv_file,
                                           names=['games',
                                                  'timestamp',
                                                  'date',
                                                  'support rank',
                                                  'support SR',
                                                  'all_damage_done',
                                                  'barrier_damage_done',
                                                  'damage_done',
                                                  'healing_done',
                                                  'deaths',
                                                  'eliminations',
                                                  'final_blows',
                                                  'objective_kills',
                                                  'objective_time',
                                                  'time_spent_on_fire',
                                                  'games_played',
                                                  'games_lost',
                                                  'games_tied',
                                                  'games_won',
                                                  'time_played',
                                                  'defensive_assists',
                                                  'offensive_assists'
                                                  ])

                if int(pandas.DataFrame(csv_file.iloc[-1:, :].values)[0]) != int(games_played):
                    logging.info("Games have been played since the last check, so writing a new line to CSV")
                    do_we_write = True
            else:
                logging.info("CSV file doesn't exist, so we need to make it")
                do_we_write = True

            if do_we_write:
                logging.info('Updating the CSV')
                with open(self.stats_csv_file, 'a', newline='') as csv_file:
                    stats_writer = csv.writer(csv_file,
                                              delimiter=',',
                                              quotechar='|',
                                              quoting=csv.QUOTE_MINIMAL)
                    stats_writer.writerow([int(games_played),
                                           ts,
                                           ds,
                                           support_comprank,
                                           support_tier,
                                           all_damage_done,
                                           barrier_damage_done,
                                           damage_done,
                                           healing_done,
                                           deaths,
                                           eliminations,
                                           final_blows,
                                           objective_kills,
                                           objective_time,
                                           time_spent_on_fire,
                                           games_played,
                                           games_lost,
                                           games_tied,
                                           games_won,
                                           time_played,
                                           defensive_assists,
                                           offensive_assists
                                           ])
            else:
                logging.info("No updates to stats")
        else:
            logging.warning("Request returned an error.")


# Main loop goes here
def main():
    ow_stats = OWstats()
    while True:
        logging.info('Going for another run')
        try:
            ow_stats.get_stats_from_api()
            ow_stats.reset_sleep_time()
        except ConnectionResetError:
            logging.exception('ConnectionResetError')
            ow_stats.increase_sleep_time()
        except KeyboardInterrupt:
            print("\n\nKeyboard exception received. Exiting.")
            logging.warning("Keyboard said to exit.")
            exit()
        except Exception:
            print("\n\nAn error in the main loop was caught.")
            logging.exception("An error in the main loop was caught")
            ow_stats.increase_sleep_time()

        print(f"sleep time: {ow_stats.sleep_time}")
        time.sleep(ow_stats.sleep_time)


try:
    if __name__ == '__main__':
        main()
except KeyboardInterrupt:
    print("\n\nKeyboard exception received. Exiting.")
    logging.warning("Keyboard said to exit.")
    exit()
except Exception:
    print("\n\nAn error in the main loop was caught.")
    logging.exception("An error in the main loop was caught")
