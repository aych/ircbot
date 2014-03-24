import re
import urllib2
import HTMLParser

class SportsStream():
    def __init__(self, irc, plugins):
        self.irc = irc
        self.plugins = plugins
        self.irc.on_command += self.handle_command
        self.sports = ['nhl', 'ahl', 'ufc', 'nba', 'pba', 'mls', 'nfl']

    def shutdown(self):
        self.irc.on_command -= self.handle_command

    def handle_command(self, destination, nick, user, host, command, params):
        if command == "STREAM.SPORTS":
            # Update the feeds.
            for s in self.sports:
                url = 'http://208.92.36.37/nlds/get_games_lte.php?client=%s' % s
                r = urllib2.Request(url=url)
                f = urllib2.urlopen(r)
                contents = f.read()
                games = contents.split(';')
                for g in games[:-1]:
                    d = g.split('|')
                    # 1 - Stream time
                    # 4 - Stream name
                    # 8 - Team 1
                    # 9 - Team 2
                    # 11 - URL
                    self.irc.privmsg(destination, "[%s] %s Stream: %s (%s vs %s) - Watch at: http://www.77zhibo.com/api/nbatv.html?id=%s" % (d[1], s, d[4], d[8], d[9], d[11].replace('rtmp','adaptive')))


def initialize(irc, plugins):
    global t
    t = SportsStream(irc, plugins)
    return True

def get_instance():
    global t
    return t

def shutdown():
    global t
    t.shutdown()
    return True