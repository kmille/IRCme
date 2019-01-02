# Simple IRC Notification framework for regular tasks

## What it does? 
1. ircme.py reads settings.yaml which contains your irc settings (server, botname, channel) and your jobs (python file + how often it should be executed e.g every 60 minutes)
2. a job is a python simple file. ireqme.py will load it during runtime and execute the go function

## If you want to try it
git clone https://github.com/kmille/IRCme.git /home/ircme/IRCme  
cd /home/ircme/IRCme  
python3 -m virtualenv venv  
source venv/bin/activate  
pip install -r requirements.txt  

## Persistence
adduser --shell /usr/sbin/nologin --disabled-password ircme  
chown -R ircme: /home/ircme/IRCme/  
cp ircme.service /etc/systemd/system  
systemctl daemon-reload  

## Configuration (check settings.yaml)
irc
    - nickname is the name of the bot
    - target can be a channel (e.g. #test123) or an irc username

jobs
    - list containing python_file and every_minutes (60 for run it every 60 minutes)

