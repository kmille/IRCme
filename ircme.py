#! /usr/bin/env python3
import os
import time
import yaml
import sys
import logging
import arrow
from threading import Thread
import importlib

import ssl
import irc.client
import schedule

from ipdb import set_trace

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IRCme:
    
    def __init__(self):
        if not ('SETTINGS' in os.environ) or not ('MODULE_PATH' in os.environ):
            logger.fatal("You have to the SETTINGS and MODULE_PATH os environment. Check the docs!")
            sys.exit(1)
        self.settings = yaml.safe_load(open(os.environ['SETTINGS']))
        self.target = self.settings['irc']['target']
        self.setup_irc()
        self.setup_jobs()
        self.reactor.process_forever()
    
    
    def setup_irc(self):
        logger.info("Connecting to irc server")
        ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        self.reactor = irc.client.Reactor()
        try:
            c = self.reactor.server().connect(
                self.settings['irc']['server'],
                self.settings['irc']['port'],
                self.settings['irc']['nickname'],
                connect_factory=ssl_factory,
            )
        except irc.client.ServerConnectionError:
            logger.fatal(sys.exc_info()[1])
            sys.exit(1)

        c.add_global_handler("welcome", self.on_connect)
        c.add_global_handler("disconnect", self.on_disconnect)

    
    def on_connect(self, connection, event):
        logger.info("Connected to irc server")
        if irc.client.is_channel(self.target):
            logger.info("Joining to channel {}".format(self.target))
            connection.join(self.target)
            logger.info("Joined")
        self.irc_connection = connection
    
    
    def on_disconnect(self, connection, event):
        logger.fatal("We got disconnected from the irc server", str(event))
        sys.exit(1)
    
    
    def setup_jobs(self):
        logger.info("Loading jobs")
        sys.path.insert(0, os.environ['MODULE_PATH'])
        for job in self.settings['jobs']:
            logger.info("Loading {}".format(job['python_file']))
            schedule.every(job['every_minutes']).minutes.do(self.do_job, job['python_file'])
        logger.info("Loaded jobs")
        t = Thread(target=self.execute_tasks, args=())
        t.start()


    def execute_tasks(self):
        while 1:
            schedule.run_pending()
            time.sleep(1)


    def do_job(self, python_file):
        logger.info("Executing job for {} at {}".format(python_file, arrow.now().format("HH:mm:ss")))
        if python_file.endswith(".py"):
            python_file = python_file[:-3]
        try:
            lib = importlib.import_module(python_file)
        except ModuleNotFoundError as e:
            logger.fatal("Could not load module {}.\n{}".format(python_file, e))
            return

        try:
            ret = lib.go()
        except Exception as e:
            logger.fatal("Error executing script.\n{}".format(e))
        
        while not hasattr(self, 'irc_connection'):
            logger.info("Waiting for irc connection")
            time.sleep(3)
        if type(ret) == list:
            for msg in ret:
                self.irc_connection.privmsg(self.target, msg)
        else:
            self.irc_connection.privmsg(self.target, ret)
        

if __name__ == '__main__':
    IRCme()
