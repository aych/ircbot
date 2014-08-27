import hashlib

PLUGIN_CLASS = 'Test'

class Test(object):
    def __init__(self, irc):
        self.irc = irc
        self.plugins = irc.plugins
        self.irc.on_privmsg += self.testfunc

    def shutdown(self):
        self.irc.on_privmsg -= self.testfunc
        return True

    def md5(self, text):
        return hashlib.md5(text).hexdigest()

    def testfunc(self, destination, nick, user, host, message):
        parts = message.split(' ')
        cmd = parts[0].upper()
        if cmd == 'MD5':
            rest = message[len(cmd) + 1:]
            self.irc.privmsg(destination, "%s" % self.md5(rest))
