import pickle
import hashlib

import string
import random

# User format:
# user.username = {
# user.flags
# user.salt
# user.password (sha512)
# user.logged_in
# user.hostmask

FLAGS_NONE = ''
FLAGS_ADMIN = 'A'
FLAGS_OPERATOR = 'O'
FLAGS_SAFELIST = 'S'
FLAGS_SHITLIST = 'Z'

class Flags(object):
    def __init__(self, flags_allow, flags_deny, default_allow):
        self.kwargs = {'flags_allow': flags_allow, 'flags_deny': flags_deny, 'default_allow': default_allow}

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            kwargs.update(self.kwargs)
            return f(*args, **kwargs)
        return wrapped_f


class Auth():
    def __init__(self, irc, plugins):
        self.plugins = plugins
        self.irc = irc
        self.auth = self
        self.auth_users = {}
        self.last_user = {}

        # Default username/password is admin/admin
        admin = {'username': 'admin',
                 'flags': 'A',
                 'salt': 'admin',
                 'password': '8450eca01665516d9aeb5317764902b78495502637c96192c81b1683d32d691a0965cf037feca'
                             + '8b9ed9ee6fc6ab8f27fce8f77c4fd9b4a442a00fc317b8237e6',
                 'logged_in': False,
                 'nickname': '',
                 'hostmask': ''}

        # Unpickle the auth list.
        try:
            self.auth_users = pickle.load(open('plugins/data/auth_users.pkl', 'rb'))
        except Exception, e:
            # First time run, create the auth file.
            pickle.dump(self.auth_users, open('plugins/data/auth_users.pkl', 'wb'))

        if 'admin' not in self.auth_users:
            self.auth_users['admin'] = admin

        # Register for fun!
        self.irc.on_command += self.handle_command
        self.irc.on_privmsg += self.handle_privmsg
        self.irc.on_nick_change += self.handle_nick_change

    def shutdown(self):
        # Remove the callbacks
        self.irc.on_command -= self.handle_command
        self.irc.on_privmsg -= self.handle_privmsg
        self.irc.on_nick_change -= self.handle_nick_change

        # Pickle the auth list.
        try:
            pickle.dump(self.auth_users, open('plugins/data/auth_users.pkl', 'wb'))
            return True
        except Exception, e:
            self.irc.set_exception(e)
            return False

    def dependency_loaded(self, module):
        if module in self.plugins:
            return True
        else:
            return False

    def handle_nick_change(self, nick, user, host, new_nick):
        if self.is_logged_in(nick, host):
            self.last_user['nickname'] = new_nick

    def handle_command(self, destination, nick, user, host, command, params):
        if command == 'IDENTIFY':
            if self.is_logged_in(nick, host):
                self.irc.privmsg(destination, 'The username "%s" is already logged in from nick %s.' %
                                              (params[1], self.last_user['username']))
                return

            # IDENTIFY <username> <password>
            if len(params) == 3:
                u = self.check_login(params[1], params[2])
                if u is not None:
                    u['logged_in'] = True
                    u['nickname'] = nick
                    u['hostmask'] = host
                    self.save_database()
                else:
                    self.irc.privmsg(destination, 'Identify command failed.')
            else:
                self.irc.privmsg(destination, 'Not enough parameters to identify.')
        elif command == 'REGISTER':
            if self.is_logged_in(nick,host):
                self.irc.privmsg(destination, 'You are already registered.')
                return
            if len(params) == 3:
                username = params[1]
                salt = self.generate_salt()
                password = hashlib.sha512(salt + params[2]).hexdigest()
                if self.has_user(username):
                    self.irc.privmsg(destination, 'The username "%s" is already registered.' % username)
                    return

                user = {'username': username,
                        'flags': '',
                        'salt': salt,
                        'password': password,
                        'logged_in': True,
                        'nickname': nick,
                        'hostmask': host}

                self.auth_users[username] = user
                self.save_database()
            else:
                self.irc.privmsg(destination, 'Format: REGISTER <username> <password>')
        elif command == 'USERS':
            self.irc.privmsg(destination, "%s" % self.auth_users)
        elif command == 'LOGOUT':
            if self.is_logged_in(nick, host):
                self.last_user['logged_in'] = False
                self.last_user['hostmask'] = ''
                self.last_user['nickname'] = ''
                self.irc.privmsg(destination, "Logged out successfully.")
                self.save_database()
            else:
                self.irc.privmsg(destination, "You are not logged in.")
        elif command == 'CHECKFLAGS':
            self.irc.privmsg(destination, "Flags: %s" % self.get_flags(params[1]))
        elif command == 'TESTPRIVS':
            self.test()
        elif command == 'CHANGEPW':
            if self.is_logged_in(nick, host):
                if len(params) > 0:
                    self.last_user['salt'] = self.generate_salt()
                    self.last_user['password'] = hashlib.sha512(self.last_user['salt'] + params[1]).hexdigest()
                    self.save_database()
        elif command == 'SETFLAGS':
            if self.is_logged_in(nick, host) and self.has_user(params[1]):
                if self.set_flags(self.last_user['username'], params[1], params[2]):
                    self.irc.privmsg(destination, 'Flags for %s: %s' % (params[1], self.get_flags(params[1])))
        elif command == 'WHOAMI':
            if self.is_logged_in(nick, host):
                self.irc.privmsg(destination,
                                 'You are logged in as %s with flags: %s' %
                                 (self.last_user['username'], self.last_user['flags']))
            else:
                self.irc.privmsg(destination, 'You are not logged in.')
        elif command == 'RMUSER':
            if self.is_logged_in(nick, host) and self.has_user(params[1]):
                self.delete_user(self.last_user['username'], params[1])

    def handle_privmsg(self, destination, nick, user, host, message):
        print "PRIVMSG: %s" % message

    def save_database(self):
        pickle.dump(self.auth_users, open('plugins/data/auth_users.pkl', 'wb'))

    def generate_salt(self, size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        return ''.join(random.choice(chars) for x in range(size))

    def check_login(self, user, password):
        if self.has_user(user):
            u = self.get_user(user)
            pw = hashlib.sha512(u['salt'] + password).hexdigest()
            if pw == u['password']:
                return u
        return None

    def has_user(self, user):
        if user in self.auth_users:
            return True
        else:
            return False

    def has_flag(self, user, flag):
        if self.has_user(user):
            if flag in self.auth_users[user]['flags']:
                return True
            else:
                return False
        else:
            return False

    def is_logged_in(self, nick, hostmask):
        for user in self.auth_users.values():
            if user['nickname'] == nick and user['hostmask'] == hostmask:
                self.last_user = user
                return True
        return False

    def get_logged_in_user(self, nick, hostmask):
        if self.is_logged_in(nick, hostmask):
            return self.last_user

    def get_user(self, user):
        if user in self.auth_users:
            return self.auth_users[user]
        else:
            return None

    def get_flags(self, user):
        if self.has_user(user):
            return self.auth_users[user]['flags']
        else:
            return ''

    def flag_allow_action(self, allow_flags, deny_flags, default_allow):
        if self.is_logged_in(self.irc.common_msg['nick'], self.irc.common_msg['host']):
            user_flags = self.last_user['flags']
            for f in deny_flags:
                if f in user_flags:
                    return False
            for f in allow_flags:
                if f in user_flags:
                    return True
        elif default_allow:
            return True
        return False

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def test(self, **kwargs):
        if self.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            self.irc.privmsg(self.irc.common_msg['destination'], 'You have access to the test command!')
        else:
            self.irc.privmsg(self.irc.common_msg['destination'], 'You don\'t have access to the test command!')

    @Flags(FLAGS_ADMIN + FLAGS_OPERATOR, FLAGS_NONE, False)
    def set_flags(self, user, target, flags, **kwargs):
        if not self.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return

        # Get the target's flags
        target_flags = self.get_flags(target)

        # Left to right scan.
        mode_add = True
        for f in flags:
            if f == '+':
                mode_add = True
            elif f == '-':
                mode_add = False
            else:
                if mode_add:
                    if f not in target_flags:
                        target_flags += f
                else:
                    if f in target_flags:
                        target_flags = target_flags.replace(f, '')
        target_flags = ''.join(sorted(target_flags))
        self.auth_users[target]['flags'] = target_flags
        return True

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def delete_user(self, user, target, **kwargs):
        if not self.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return
        del self.auth_users[target]
        

def initialize(irc, plugins):
    try:
        global plugin_auth
        plugin_auth = Auth(irc, plugins)
        return True
    except Exception, e:
        irc.set_exception(e)
        return False

def get_instance():
    global plugin_auth
    return plugin_auth

def shutdown():
    global plugin_auth
    plugin_auth.shutdown()
    return True
