import datetime
import logging
import sys
import time
from socket import gaierror

import urllib3

from owstats import CompStats, User, db
from owstats.utils import get_api_response

logging.basicConfig(filename=f'OWstats-{datetime.datetime.now().strftime("%Y-%m")}.log',
                    level=logging.INFO,
                    format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %X'
                    )


MINUTES_TO_SLEEP = 120


class OWstats:
    sleep_time = 60 * MINUTES_TO_SLEEP  # number of minutes to wait until the next run
    sleep_time_extended = False

    def increase_sleep_time(self):
        self.sleep_time = self.sleep_time + 60 * 15
        self.sleep_time_extended = True

    def reset_sleep_time(self):
        self.sleep_time = 60 * MINUTES_TO_SLEEP

    def log_stats_to_db(self):
        logging.info('DB stats call')
        for user in User.query.filter_by(active=1).all():
            platform = user.platform
            region = user.region
            username = user.username

            logging.info(f'processing: {platform}/{region}/{username}')

            try:
                response = get_api_response(platform, region, username)
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
                    # print(r_json)

                    if 'error' in r_json:
                        logging.error(f"Request error: {r_json['error']}")
                        if r_json['error'] == "Player not found":
                            user.active = 0
                            db.session.commit()
                            break
                    
                    if r_json['private']:
                            user.active = 0
                            db.session.commit()
                            break

                    games_played = r_json['competitiveStats']['games']['played']

                    if user.games_played != games_played:
                        cs = CompStats()
                        cs.games_played = games_played
                        cs.games_won = r_json['competitiveStats']['games']['won']
                        cs.rating_avg = r_json['rating']
                        for rating in r_json['ratings']:
                            if rating['role'] == 'tank':
                                cs.rating_tank = rating['level']
                            if rating['role'] == 'damage':    
                                cs.rating_damage = rating['level']
                            if rating['role'] == 'support': 
                                cs.rating_support = rating['level']
                        
                        cs.player = user

                        db.session.add(cs)
                        db.session.commit()

                        user.games_played = games_played
                        user.endorsement = r_json['endorsement']
                        user.icon = r_json['icon']
                        db.session.commit()

                except KeyError:
                    print('\n\nKeyError - API mapping issue?')
                    # logging.error('KeyError - API mapping issue?')
                    logging.exception('KeyError - API mapping issue?')
                    return           



# Main loop goes here
def main():
    ow_stats = OWstats()
    while True:
        logging.info('Going for another run')
        try:
            ow_stats.log_stats_to_db()
            if len(sys.argv) > 1 and sys.argv[1] == '-c':
                ow_stats.reset_sleep_time()
            else:
                logging.info('Run finished, exiting.')
                return
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
