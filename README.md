# OWstats
Simple script for collecting Overwatch stats. 

## Motivation
The Overwatch trackers I found online don't seem to keep long term stats, so I decided to make a little app to keep track of my own stats and share it with the world. 

## Usage
For now, this is just a command line script that runs until killed. You'll need to have python installed as well as the included packages. 

1. Download the script
2. In your environment variables add OW_USERNAME variable and set the value to your OW username. Currently the script only supports PSN.
3. Open a command prompt in the directory where you've put the script
4. Run the script with:

`python .\OWstats.py`

This will create a file OWstats.csv with your stats. I'm a support main, so I think I've set it up to collect only support SR stats.

## Credits

This scrilt is hitting the OWAPI at https://owapi.net which is processing the data from the official OW website and converting it to JSON. 
More info about their project can be found here: https://github.com/Fuyukai/OWAPI

## To-Do

- Add other platforms 
- Add other roles
- Convert to using a database (maybe SQLite?)
- Enable tracking multiple accounts
- Add some visualisation of data
