import re
import urllib2
import threading

class BTC():
    def __init__(self, irc, plugins):
        self.irc = irc
        self.plugins = plugins
        self.irc.on_command += self.handle_command
        self.current_price = ''
        self.high_price = ''
        self.low_price = ''
        self.destination = ''
        self.is_running = False

    def shutdown(self):
        self.irc.on_command -= self.handle_command
        if self.is_running:
            self.repeat_timer.cancel()

    def request_btc(self):
        r = urllib2.Request(url='https://mtgox.com')
        f = urllib2.urlopen(r)
        contents = f.read()
        p = re.search("Last price:<span>(.+?)</span>", contents, re.DOTALL).group(1)
        hp = re.search("High:<span>(.+?)</span>", contents, re.DOTALL).group(1)
        lp = re.search("Low:<span>(.+?)</span>", contents, re.DOTALL).group(1)
        if self.current_price != p or self.high_price != hp or self.low_price != lp:
            self.irc.privmsg(self.destination, "Current: %s - High: %s - Low: %s" % (p, hp, lp))
            self.current_price = p
            self.high_price = hp
            self.low_price = lp
        #self.repeat_timer = threading.Timer(10.0, self.request_btc).start()
        #self.is_running = True

    def handle_command(self, destination, nick, user, host, command, params):
        if command == 'BTC.MONITOR':
            self.destination = destination
            if self.is_running:
                self.repeat_timer.cancel()
            else:
                self.request_btc()
            #self.repeat_timer = threading.Timer(10.0, self.request_btc).start()
            #self.is_running = True
        elif command == 'TEST':
            r = urllib2.Request(url='http://blockchain.info/address/%s' % params[1])
            contents = urllib2.urlopen(r).read()
            print contents
            b = re.search('<td id="final_balance"><font color="green"><span data-c="(.+?)">(.+?) BTC</span></font></td>', contents, re.DOTALL).group(1)
            self.irc.privmsg(destination, b)

def initialize(irc, plugins):
    global b
    b = BTC(irc, plugins)
    return True

def get_instance():
    global b
    return b

def shutdown():
    global b
    b.shutdown()
    return True