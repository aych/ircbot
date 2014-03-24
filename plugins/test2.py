import hashlib
from auth import Flags, FLAGS_ADMIN, FLAGS_NONE

class Test2():
    def __init__(self, irc, plugins):
        self.plugins = plugins
        self.irc = irc
        self.irc.on_privmsg += self.testfunc
        self.auth = plugins['auth'].get_instance()

    def shutdown(self):
        self.irc.on_privmsg -= self.testfunc

    def dependency_loaded(self, module):
        if module in self.plugins:
            return True
        else:
            return False

    @Flags(FLAGS_ADMIN, FLAGS_NONE)
    def testfunc(self, destination, nick, user, host, message, flags_allow=FLAGS_NONE, flags_deny=FLAGS_NONE):
        parts = message.split(' ')
        cmd = parts[0].upper()
        rest = message[len(cmd) + 1:]
        if cmd == 'SHA224':
            if self.auth.is_logged_in(nick, host):
                ret = self.auth.flag_allow_action(self.auth.last_user['flags'], flags_allow, flags_deny)
                if ret:
                    self.irc.privmsg(destination, "%s" % hashlib.sha224(rest).hexdigest())
        if cmd == 'MD5':
            if self.dependency_loaded('test'):
                try:
                    test = self.plugins['test'].get_instance()
                    self.irc.privmsg(destination, "[test2] %s" % test.md5(rest))
                except Exception, e:
                    self.irc.privmsg(destination, "%s" % e)
            else:
                self.irc.privmsg(destination, "Dependency on 'test' module not met")

def initialize(irc, plugins):
    try:
        global t
        t = Test2(irc, plugins)
        return True
    except Exception, e:
        irc.set_exception(e)
        return False

def get_instance():
    global t
    return t

def shutdown():
    global t
    t.shutdown()
    return True