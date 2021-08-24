# OWstats
Simple script for collecting Overwatch stats. 

## Motivation
The Overwatch trackers I found online don't seem to keep long term stats, so I decided to make a little app to keep track of my own stats and share it with the world. 

## Usage
For now, this is just a command line script that runs until killed. It doesn't have a pretty way to add users, but I'm woring on a web interface that will allow you to easily add users and see their stats.  


## Credits

This scrilt is hitting the OWAPI at https://ow-api.com which is processing the data from the official OW website and converting it to JSON. 

## Recent changes

### 2021-08-24

- Added carts for data visualization
- Added win percentage
- Added command line args so it can run as cron job
- Error logging, inactive users, endorsment & icon
- Grayed out inactive users
- DB string in environment variable

### 2021-07-24

- Added a Flask & Bulma interface to easily see users and stats
- Added the ability to add users through the interface

### 2021-07-20

- Switched from using a CSV file to using SQLite database. 
- Switched from https://owapi.net to https://ow-api.com
- Tracking all platforms and roles (only role queue)
- Tracking only SR and games played and won, no other stats. 
- Tracking multiple users


## To-Do

- Add documentation to make installation and usage easy

## Done

- Add some visualisation of data
- Add an interface for adding users and viewing stats
- Add other platforms 
- Add other roles
- Convert to using a database (maybe SQLite?)
- Enable tracking multiple accounts
