from functools import wraps
import errno
import os
import signal
import re
from collections import deque

PLUGIN_CLASS = 'ChannelBuffer'

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,seconds) #used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

class ChannelBuffer():
    def __init__(self, irc):
        self.irc = irc
        self.plugins = irc.plugins
        self.buffer = {}
        self.buffer_size = 500

        self.irc.on_privmsg += self.handle_privmsg
        self.irc.on_command += self.handle_command

    def shutdown(self):
        self.irc.on_privmsg -= self.handle_privmsg
        self.irc.on_command += self.handle_command
        return True

    def color(self, text):
        text = text.replace('{bold}', '\x02')
        text = text.replace('{reset}', '\x03')
        text = text.replace('{white}', '0')
        text = text.replace('{black}', '1')
        text = text.replace('{darkblue}', '2')
        text = text.replace('{darkgreen}', '3')
        text = text.replace('{red}', '4')
        text = text.replace('{maroon}', '5')
        text = text.replace('{purple}', '6')
        text = text.replace('{orange}', '7')
        text = text.replace('{yellow}', '8')
        text = text.replace('{green}', '9')
        text = text.replace('{darkcyan}', '10')
        text = text.replace('{cyan}', '11')
        text = text.replace('{blue}', '12')
        text = text.replace('{magenta}', '13')
        text = text.replace('{gray}', '14')
        text = text.replace('{silver}', '15')
        text = re.sub('\[([0-9,]{1,5})]', '\x03\\1', text)
        return text

    def handle_privmsg(self, destination, nick, user, host, message):
        if destination[0] == '#':
            if destination not in self.buffer:
                self.buffer[destination] = deque()
            if not message.startswith('s/'):
                self.buffer[destination].append({'nick': nick, 'user': user, 'host': host, 'message': message})
            if len(self.buffer[destination]) > self.buffer_size:
                self.buffer[destination].popleft()

        if message[0:2] == 's/':
            parts = message.split('/')
            regex = parts[1]
            replace_with = parts[2]
            if len(parts) > 3:
                flags = parts[3]
            else:
                flags = ''

            # Find if the line exists in the buffer.
            try:
              ret = self.regex_seek_in_buffer(destination, 'message', regex, 'i' in flags)
              if ret is not None:
                  msg = ret['message']
                  if 'i' in flags:
                      m = re.search(regex, msg, re.IGNORECASE)
                  else:
                      m = re.search(regex, msg)
                  if m is not None:
                      #if 'g' in flags:
                      #    msg = msg.replace(m.group(), replace_with)
                      #else:
                      #    msg = msg.replace(m.group(), replace_with, 1)
                      #if len(msg) > 255:
                      #  msg = msg[0:255]
                      msg = re.sub(regex, replace_with, msg)
                      self.irc.privmsg(destination, self.color('<{bold}%s{bold}> %s' % (ret['nick'], msg)))
                  else:
                      pass
              else:
                  pass
            except Exception, e:
              self.irc.privmsg(destination, "Timed out on regex search.")

    def handle_command(self, destination, nick, user, host, command, params):
        if command == 'SEEK':
            ret = self.seek_in_buffer(destination, params[1], params[2])
            if ret is not None:
                print "Sending to IRC -> %s" % ret
                self.irc.privmsg(destination, "Found: <%s> %s" % (ret['nick'], ret['message']))

    def has_buffer(self, channel):
        if channel in self.buffer:
            return True
        else:
            return False

    def get_buffer(self, channel):
        if self.has_buffer(channel):
            return self.buffer[channel]
        else:
            return None

    def seek_in_buffer(self, channel, param, needle):
        if self.has_buffer(channel):
            tmp = self.buffer[channel]
            for i in range(-2, 0 - len(tmp) - 1, -1):
                if needle in tmp[i][param]:
                    return tmp[i]
        return None

    @timeout(1.0)
    def regex_seek_in_buffer(self, channel, param, needle, case_insensitive=False):
        if self.has_buffer(channel):
            tmp = self.buffer[channel]
            for i in range(-1, 0 - len(tmp) - 1, -1):
                if case_insensitive:
                    m = re.search(needle, tmp[i][param], re.IGNORECASE)
                else:
                    m = re.search(needle, tmp[i][param])
                if m is not None:
                    return tmp[i]
        return None
