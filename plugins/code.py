import subprocess
import sys
import StringIO

from auth import Flags, FLAGS_ADMIN, FLAGS_NONE

PLUGIN_CLASS = 'Code'

class Code(object):
    def __init__(self, irc):
        self.irc = irc
        self.plugins = irc.plugins
        self.irc.on_command += self.handle_command
        self.auth = self.plugins['auth']
        self.recording = False
        self.recording_nick = ''
        self.console_mode = False

    def shutdown(self):
        self.irc.on_command -= self.handle_command
        return True

    def handle_command(self, destination, nick, user, host, command, params):
        # self.irc.privmsg(destination, "code.handle_command(%s)" % command)
        if self.console_mode and not self.recording and command != 'CONSOLE.END':
            cmd = ' '.join(params)
            if cmd[0] == '$':
                cmd = cmd[1:]
            else:
                return
            ret = self.execute_console(cmd)
            if ret:
                for l in ret:
                    self.irc.privmsg(destination, l)
        else:
            if command == 'EXEC':
                message = ' '.join(params[1:])
                try:
                    self.execute_code(message)
                except Exception, e:
                    self.irc.privmsg(destination, "Exception: %s" % e)
            elif command == "CONSOLE.BEGIN":
                self.console_mode = True
                self.irc.privmsg(destination, 'Entering console mode...')
            elif command == "CONSOLE.END":
                self.console_mode = False
                self.irc.privmsg(destination, 'Entering console mode...')
            elif command == 'CODE.BEGIN':
                if self.recording:
                    self.irc.privmsg(destination,
                                     "A coding session is already in progress, owned by %s" % self.recording_nick)
                    return
                self.recording = True
                self.recording_nick = nick
                self.recorded_buffer = []
                self.irc.privmsg(destination, "A coding session has been opened for %s" % self.recording_nick)
            elif command == 'CODE.END':
                if not self.recording:
                    self.irc.privmsg(destination, "There is no currently active coding session.")
                    return
                if nick != self.recording_nick:
                    self.irc.privmsg(destination, "You don't own the active coding session.")
                    return
                self.irc.privmsg(destination, "Ending %s's coding session" % self.recording_nick)
                try:
                    print "\n".join(self.recorded_buffer)
                    self.execute_code("\n".join(self.recorded_buffer))
                except Exception, e:
                    self.irc.privmsg(destination, "Exception: %s" % e)
                self.recording = False
                self.recording_nick = ''
                self.recorded_buffer = []
            elif self.recording and self.recording_nick == nick:
                self.recorded_buffer.append(' '.join(params))

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def execute_console(self, cmd, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return False

        retVal = subprocess.Popen(cmd, shell=True,
                                  stdout=subprocess.PIPE).stdout.read().strip('\n').split('\n')
        if retVal == ['']:
            return False
        else:
            return retVal

    @Flags(FLAGS_ADMIN, FLAGS_NONE, False)
    def execute_code(self, code, **kwargs):
        if not self.auth.flag_allow_action(kwargs['flags_allow'], kwargs['flags_deny'], kwargs['default_allow']):
            return False

        codeOut = StringIO.StringIO()
        codeErr = StringIO.StringIO()

        code = 'exec """%s"""' % code

        sys.stdout = codeOut
        sys.stderr = codeErr

        exec code

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        s = codeOut.getvalue()
        ss = s.split("\n")
        for s in ss:
            if len(s) > 0:
                self.irc.privmsg(self.irc.common_msg['destination'], s)
        s = codeErr.getvalue()
        if len(s) > 0:
            self.irc.privmsg(self.irc.common_msg['destination'], "Error: %s" % s)
