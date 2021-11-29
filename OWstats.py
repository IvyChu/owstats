import datetime
import logging
import sys
import time
from socket import gaierror

import urllib3

from owstats import CompStats, Season, User, db
from owstats.utils import (check_if_more_than_seven_days, get_api_response,
                           is_it_monday, is_it_new_season, make_plot)

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

    def set_season(self, season_no):
        new_season = Season()
        new_season.season = season_no
        db.session.add(new_season)
        db.session.commit()
        print("Season set successfully.")

    def set_next(self, season_end):
        season_end_date = datetime.datetime.strptime(season_end, "%Y/%m/%d")
        current_season = Season.query.order_by(Season.etime.desc()).first()
        current_season.next_switch_date = season_end_date
        db.session.commit()
        print(f"Season end set successfully to {season_end}.")

    def current(self):
        current_season = Season.query.order_by(Season.etime.desc()).first()
        print(current_season)

    def log_stats_to_db(self):
        logging.info('DB stats call')

        # What season is it?
        current_season = Season.query.order_by(Season.etime.desc()).first()

        # make list of users that need to be processed
        users = User.query.filter_by(active=1).order_by(User.etime.desc()).all()

        # if it's the first run on Monday, check if any of inactive players played in the last week
        if is_it_monday():
            users = users + User.query.filter_by(active=2).all()    # inactive
            users = users + User.query.filter_by(active=3).all()    # private
            users = users + User.query.filter_by(active=0).all()    # error
            

        # get stats for active players
        for user in users:
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
                        else:
                            logging.error(f"json.error: {r_json['error']}")
                            break
                    
                    if r_json['private']:
                        user.active = 3
                        db.session.commit()
                        break

                    games_played = r_json['competitiveStats']['games']['played']

                    if user.games_played != games_played:
                        
                        # if there are no placements at all, there is no need to log this
                        if r_json['rating'] == 0:
                            break

                        # is it a new season for this user
                        if games_played < user.games_played:

                            # is it a new season for everyone?
                            if is_it_new_season(current_season.next_switch_date):
                                # it's a new season, so we're making a new one!
                                new_season = Season()
                                new_season.season = current_season.season + 1
                                db.session.add(new_season)
                                db.session.commit()
                                current_season = new_season

                        cs = CompStats()

                        cs.season = current_season.season
                        cs.games_played = games_played
                        cs.games_won = r_json['competitiveStats']['games']['won']
                        cs.rating_avg = r_json['rating']
                        if 'ratings' in r_json and r_json['ratings'] is not None:
                            for rating in r_json['ratings']:
                                if rating['role'] == 'tank':
                                    cs.rating_tank = rating['level'] or None
                                if rating['role'] == 'damage':
                                    cs.rating_damage = rating['level'] or None
                                if rating['role'] == 'support':
                                    cs.rating_support = rating['level'] or None
                        else:
                            cs.rating_tank = None
                            cs.rating_damage = None
                            cs.rating_support = None
                        
                        cs.player = user

                        db.session.add(cs)
                        db.session.commit()

                        user.games_played = games_played
                        user.active = 1
                        user.endorsement = r_json['endorsement']
                        user.icon = r_json['icon']
                        db.session.commit()

                        make_plot(user)
                    elif check_if_more_than_seven_days(user.comp_stats[0].ctime):
                        user.active = 2     # inactive for a week or more
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
            if len(sys.argv) > 1:
                if len(sys.argv) == 3 and sys.argv[1] == 'set-season':
                    ow_stats.set_season(int(sys.argv[2]))
                    return

                if len(sys.argv) > 1 and sys.argv[1] == 'current':
                    ow_stats.current()
                    return

                if len(sys.argv) == 3 and sys.argv[1] == 'set-next':
                    ow_stats.set_next(sys.argv[2])
                    return

                if len(sys.argv) > 1 and sys.argv[1] in ['-h','--help']:
                    a ="""Usage: OWstats [OPTIONS] COMMAND [ARGS]...

  Hits the Overwatch API and updates stats for all active players in the database.

Options:
  -h, --help  Show this message and exit.
  -c          Run continuously in console, don't exit after one run.

Commands:
  set-season      Creates a new season entry in seasons table
  current         Display the current season in the database
  set-next        Set the season switch date 
                """
                    if len(sys.argv) == 3:
                        if sys.argv[2] == 'set-season':
                            a = """Usage: OWstats set-season TEXT

  Creates a new season entry in seasons table with season=TEXT
                        """
                        if sys.argv[2] == 'current':
                            a = """Usage: OWstats current

  Prints the current season from the database.
                        """

                        if sys.argv[2] == 'set-next':
                            a = """Usage: OWstats set-next DATE

  Updates the current season's next_switch_date to DATE. DATE should be in YYYY/MM/DD format.
                    
                        """
                    print(a)  
                    return  
        except Exception:
            logging.exception("An error was caught")
            return


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
