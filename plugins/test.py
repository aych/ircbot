import hashlib

class Test():
    def __init__(self, irc, plugins):
        self.irc = irc
        self.plugins = plugins
        self.irc.on_privmsg += self.testfunc

    def shutdown(self):
        self.irc.on_privmsg -= self.testfunc

    def md5(self, text):
        return hashlib.md5(text).hexdigest()

    def testfunc(self, destination, nick, user, host, message):
        parts = message.split(' ')
        cmd = parts[0].upper()
        if cmd == 'MD5':
            rest = message[len(cmd) + 1:]
            self.irc.privmsg(destination, "%s" % self.md5(rest))

def initialize(irc, plugins):
    global t
    t = Test(irc, plugins)
    return True

def get_instance():
    global t
    return t

def shutdown():
    global t
    t.shutdown()
    return True