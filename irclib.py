import string
from SimpleTCPClient import SimpleTCPClient

NEWLINE = "\r\n"

class Event(object):
    def __init__(self, func):
        self.__doc__ = func.__doc__
        self._key = '__Event_' + func.__name__

    def __get__(self, obj, cls):
        try:
            return obj.__dict__[self._key]
        except KeyError:
            d = obj.__dict__[self._key] = Delegate()
            return d


class Delegate(object):
    def __init__(self):
        self._fns = []

    def __iadd__(self, fn):
        self._fns.append(fn)
        return self

    def __isub__(self, fn):
        self._fns.remove(fn)
        return self

    def __call__(self, *args, **kwargs):
        for f in self._fns[:]:
            f(*args, **kwargs)
    #     try:
    #         f(*args, **kwargs)
    #     except Exception, e:
    #         print "%s" % e


class IRCClient(SimpleTCPClient):
  def __init__(self):
    super(IRCClient, self).__init__()
    self.buffer = ''
    self.exception = None
    self.common_msg = {}
    self.registered = 0

    self.nickname = ''
    self.username = ''
    self.real_name = ''

    self.current_nickname = ''

  def set_exception(self, ex):
    self.exception = ex

  def irc_connect(self, host, port, nickname, username, real_name):
    self.host = host
    self.port = port
    self.registered = 0

    self.nickname = nickname
    self.username = username
    self.real_name = real_name

    self.current_nickname = nickname

    super(IRCClient, self).connect(host, port)

  def on_recv(self, data):
    self.buffer += data

    while NEWLINE in self.buffer:
      parts = self.buffer.split(NEWLINE, 1)
      self.buffer = parts[1]
      self.on_packet(parts[0])

  def send_data(self, data):
    data = "%s%s" % (data, NEWLINE)
    print "--- SEND ---"
    hexdump(data, ' ', 16)
    self.push(data)

  def register(self):
    if self.registered == 0:
      self.registered = 1
      self.send_data("NICK %s" % self.nickname)
      self.send_data("USER %s 8 * :%s" % (self.username, self.real_name))

  def change_nick(self, new_nick):
    self.send_data("NICK %s" % new_nick)

  def join_channel(self, channel):
    self.send_data("JOIN %s" % channel)

  def part_channel(self, channel):
    self.send_data("PART %s" % channel)

  def quit_irc(self, message):
    self.send_data("QUIT :%s" % message)

  def privmsg(self, destination, message):
    self.send_data("PRIVMSG %s :%s" % (destination, message))

  def notice(self, destination, message):
    self.send_data("NOTICE %s :%s" % (destination, message))

  def on_packet(self, packet):
    print "--- RECV ---"
    hexdump(packet, ' ', 16)

    params = packet.split(':')
    if len(params[0]) == 0:
      cmdparams = params[1].split(' ')
      rest = packet[packet.find(':', 2) + 1:]
      cmd = cmdparams[1]
      if cmd.isdigit():
        if cmd == "001":
          self.common_msg['message'] = rest
          self.on_server_welcome(rest)
        elif cmd == "002":
          self.common_msg['message'] = rest
          self.on_server_info(rest)
        elif cmd == "003":
          self.common_msg['message'] = rest
          self.on_server_created(rest)
        elif cmd == "004":
          self.on_logged_in()
        elif cmd == "005":
          # Server supports...
          pass
        elif cmd == "251":
          self.common_msg['message'] = rest
          self.on_network_information(rest)
        elif cmd == "252":
          self.common_msg['message'] = cmdparams[3]
          self.on_operators_online(cmdparams[3])
        elif cmd == "254":
          self.common_msg['message'] = cmdparams[3]
          self.on_channels_formed(cmdparams[3])
        elif cmd == "255":
          self.common_msg['message'] = rest
          self.on_specific_server_info(rest)
        elif cmd == "265":
          self.common_msg['message'] = rest
          self.on_local_users(rest)
        elif cmd == "266":
          self.common_msg['message'] = rest
          self.on_global_users(rest)
        elif cmd == "311":
          self.common_msg['nick'] = cmdparams[3]
          self.common_msg['user'] = cmdparams[4]
          self.common_msg['host'] = cmdparams[5]
          self.common_msg['message'] = rest   # real name
          self.on_whois_info(cmdparams[3], cmdparams[4], cmdparams[5], rest)
        elif cmd == "332":
          self.common_msg['destination'] = cmdparams[3]
          self.common_msg['message'] = rest
          self.on_topic_is(cmdparams[3], rest)
        elif cmd == "333":
          self.common_msg['destination'] = cmdparams[3]
          self.common_msg['nick'] = cmdparams[4]
          self.common_msg['message'] = cmdparams[5]
          self.on_topic_set_by(cmdparams[3], cmdparams[4], cmdparams[5])
        elif cmd == "353":
          names = rest.split(' ')
          for name in names:
            if len(name) > 0:
              self.common_msg['destination'] = cmdparams[4]
              self.common_msg['nick'] = name
              self.on_name_in_channel(cmdparams[4], name)
        elif cmd == "366":
          self.on_end_of_names()
        elif cmd == "372":
          self.common_msg['message'] = rest
          self.on_motd_data(rest)
        elif cmd == "375":
          self.common_msg['message'] = rest
          self.on_motd_begin(rest)
        elif cmd == "376":
          self.common_msg['message'] = rest
          self.on_motd_end(rest)
        elif cmd == "401":
          self.common_msg['destination'] = cmdparams[3]
          self.common_msg['message'] = rest
          self.on_no_such_nick_channel(cmdparams[3], rest)
        elif cmd == "433":
          self.on_nickname_in_use()
        else:
          print '-> UNRECOGNIZED NUMERIC <-'
      else:
        identifiers = cmdparams[0]
        if '!' in identifiers:
          nick = identifiers.split('!')[0]
          user = identifiers.split('!')[1].split('@')[0]
          host = identifiers.split('!')[1].split('@')[1]
          self.common_msg['nick'] = nick
          self.common_msg['user'] = user
          self.common_msg['host'] = host
        else:
          nick = ''
          user = ''
          host = ''

        if cmdparams[1] == '---':
          pass
        elif cmdparams[1] == 'JOIN':
          self.common_msg['destination'] = rest
          self.on_join(rest, nick, user, host)
        elif cmdparams[1] == 'MODE':
          self.common_msg['destination'] = cmdparams[2]
          self.common_msg['message'] = rest = ' '.join(cmdparams[3:])
          if nick == '':
            nick = cmdparams[0]
          self.on_mode_change(nick, user, host, cmdparams[2], rest)
        elif cmdparams[1] == 'NICK':
          self.common_msg['message'] = rest
          self.on_nick_change(nick, user, host, rest)
          if nick == self.current_nickname:
            self.current_nickname = rest
        elif cmdparams[1] == 'NOTICE':
          self.common_msg['destination'] = cmdparams[2]
          self.common_msg['message'] = rest
          self.on_notice(cmdparams[2], rest)
          if cmdparams[2] == 'AUTH':
            self.register()
        elif cmdparams[1] == 'PART':
          self.common_msg['destination'] = rest
          self.on_part(rest, nick, user, host)
        elif cmdparams[1] == 'PRIVMSG':
          # When queried, this makes the person who queried you the 'destination'
          # parameter rather than your own nick. Took an awesome infinite loop
          # before I figured that out.
          if cmdparams[2] == self.current_nickname:
            cmdparams[2] = nick
          self.common_msg['destination'] = cmdparams[2]
          self.common_msg['message'] = rest
          self.on_privmsg(cmdparams[2], nick, user, host, rest)
          if len(rest) > 0:
            parts = rest.split(' ')
            cmd = parts[0].upper()
            self.on_command(cmdparams[2], nick, user, host, cmd, parts)
        elif cmdparams[1] == 'QUIT':
          self.common_msg['message'] = rest
          self.on_quit(nick, user, host, rest)
        elif cmdparams[1] == 'TOPIC':
          self.common_msg['destination'] = cmdparams[2]
          self.common_msg['message'] = rest
          self.on_topic(cmdparams[2], nick, user, host, rest)
        else:
          print '-> UNRECOGNIZED NON-NUMERIC <-'
    else:
      cmd = params[0].rstrip(None)

      if cmd == 'PING':
        self.send_data("PONG %s" % params[1])
      else:
        print '-> UNRECOGNIZED NON-COMMAND <-'

  @Event
  def on_connected(self, host, port):
    pass
  
  @Event
  def on_disconnected(self):
    pass
  
  @Event
  def on_socket_error(self):
    pass
  
  @Event
  def on_server_welcome(self, rest):
    pass

  @Event
  def on_server_info(self, rest):
    pass

  @Event
  def on_server_created(self, rest):
    pass

  @Event
  def on_logged_in(self):
    pass

  @Event
  def on_network_information(self, rest):
    pass
  
  @Event
  def on_operators_online(self, rest):
    pass
  
  @Event
  def on_channels_formed(self, rest):
    pass

  @Event
  def on_specific_server_info(self, rest):
    pass
  
  @Event
  def on_local_users(self, rest):
    pass
  
  @Event
  def on_global_users(self, rest):
    pass
  
  @Event
  def on_whois_info(self, nick, user, host, real_name):
    pass
  
  @Event
  def on_topic_is(self, channel, topic):
    pass
  
  @Event
  def on_topic_set_by(self, channel, nick, timestamp):
    pass
  
  @Event
  def on_name_in_channel(self, channel, name):
    pass
  
  @Event
  def on_end_of_names(self):
    pass
  
  @Event
  def on_motd_data(self, rest):
    pass
  
  @Event
  def on_motd_begin(self, rest):
    pass
  
  @Event
  def on_motd_end(self, rest):
    pass
  
  @Event
  def on_no_such_nick_channel(self, param1, rest):
    pass
  
  @Event
  def on_nickname_in_use(self):
    pass
  
  @Event
  def on_join(self, rest, nick, user, host):
    pass
  
  @Event
  def on_mode_change(self, nick, user, host, destination, modes):
    pass

  @Event
  def on_nick_change(self, nick, user, host, new_nick):
    pass
  
  @Event
  def on_notice(self, destination, message):
    pass
  
  @Event
  def on_part(self, param1, nick, user, host):
    pass

  @Event
  def on_privmsg(self, destination, nick, user, host, message):
    pass

  @Event
  def on_command(self, destination, nick, user, host, command, params):
    pass
  
  @Event
  def on_quit(self, nick, user, host, rest):
    pass
  
  @Event
  def on_topic(self, param1, nick, user, host, rest):
    pass


def hexdump(chars, sep, width):
  while chars:
    line = chars[:width]
    chars = chars[width:]
    line = line.ljust(width, '\000')
    print "%s%s%s" % (sep.join("%02x" % ord(c) for c in line),
              sep, quotechars(line))


def quotechars(chars):
  return ''.join(['.', c][c in string.printable] for c in chars)
