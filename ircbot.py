import imp
import os
import sys

from irclib import IRCClient
import config

from plugins.auth import Flags, FLAGS_ADMIN, FLAGS_NONE


class IRCBot(IRCClient):
    def __init__(self):
        super(IRCBot, self).__init__()
        self.plugins = {}

        # We require auth, so might as well load it.
        # TODO: Make plugins to load at runtime part of the config.
        for plugin in config.AUTOLOAD:
            self.internal_load(plugin)
        if 'auth' in self.plugins:
            self.auth = self.plugins['auth']

        self.on_disconnected += self.irc_disconnected
        self.on_logged_in += self.irc_logged_in
        self.on_privmsg += self.irc_privmsg
        self.on_nickname_in_use += self.irc_nickname_in_use

    def connect(self):
        #try:
        self.current_nick = config.IRC_NICK

        self.irc_connect(config.IRC_SERVER,
                         config.IRC_PORT,
                         config.IRC_NICK,
                         config.IRC_USERNAME,
                         config.IRC_REALNAME)
        #except OSError, e:
        #self.irc_disconnected()
        #except Exception, e:
        #    exc_type, exc_obj, exc_tb = sys.exc_info()
        #    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #    print(exc_type, fname, exc_tb.tb_lineno)


    def internal_load(self, plugin):
        if plugin in self.plugins:
            return False
        try:
            _file, _path, _description = imp.find_module(plugin, ['plugins/'])
        except ImportError:
            return False
        obj = None
        try:
            obj = imp.load_module(plugin, _file, _path, _description)
        except Exception, e:
            return False
        try:
            plugin_name = obj.PLUGIN_CLASS
            plugin_obj = getattr(obj, plugin_name)
            plugin_instance = plugin_obj(self)
            self.plugins[plugin] = plugin_instance
            return True
        except Exception, e:
            print "%s failed to load: %s" % (plugin, e)
        return False

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def load_plugin(self, plugin, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return False

        return self.internal_load(plugin)

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def unload_plugin(self, plugin, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return
        destination = self.common_msg['destination']
        if plugin in self.plugins:
            if self.plugins[plugin].shutdown():
                pass
            else:
                self.privmsg(destination, "Shutdown during unload failed for %s" % plugin)
            self.privmsg(destination, "%s unloaded" % plugin)
            del(sys.modules[plugin])
            self.plugins.pop(plugin, None)
        else:
            self.privmsg(destination, "%s wasn't loaded" % plugin)

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def join_channel(self, channel, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return
        super(IRCBot, self).join_channel(channel)

    @Flags(FLAGS_ADMIN, FLAGS_NONE, True)
    def list_plugins(self, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return
        self.privmsg(self.common_msg['destination'], "Plugins loaded: %s" % self.plugins.keys())

    def irc_nickname_in_use(self):
        if self.current_nick == config.IRC_NICK:
            self.current_nick = config.IRC_ALT_NICK
            self.change_nick(config.IRC_ALT_NICK)
        else:
            self.current_nick = config.IRC_NICK
            self.change_nick(config.IRC_NICK)

    def irc_privmsg(self, destination, nick, user, host, message):
        parts = message.split(' ')
        cmd = parts[0].upper()

        if cmd == 'LOAD':
            plugin = parts[1]
            if self.load_plugin(plugin):
                self.privmsg(destination, "Plugin loaded: %s" % plugin)
        elif cmd == 'UNLOAD':
            plugin = parts[1]
            self.unload_plugin(plugin)
        elif cmd == 'RELOAD':
            plugin = parts[1]
            if plugin in self.plugins:
                self.unload_plugin(plugin)
            if self.load_plugin(plugin):
                self.privmsg(destination, "Plugin loaded: %s" % plugin)
        elif cmd == 'PLUGINS':
            self.list_plugins()
        elif cmd == 'JOIN':
            self.join_channel(parts[1])

    def irc_logged_in(self):
        [super(IRCBot, self).join_channel(c) for c in config.AUTOJOIN]

    def irc_disconnected(self):
        print "Disconnected."
        self.connect()

if __name__ == '__main__':
  irc = IRCBot()
  irc.connect()
