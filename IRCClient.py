from SimpleTCPClient import SimpleTCPClient

class IRCClient(SimpleTCPClient):
  def __init__(self):
    super(IRCClient, self).__init__()
    self.buffer = ''

  def connect(self, host, port):
    super(IRCClient, self).connect(host, port)

  def on_connect(self, host, port):
    pass

  def on_disconnect(self):
    pass

  def on_error(self, e):
    pass

  def on_recv(self, data):
    self.buffer += data

    while "\r\n" in self.buffer:
      parts = self.buffer.split("\r\n", 1)
      self.buffer = parts[1]
      self.on_packet(parts[0])

  def on_packet(self, packet):
    print packet

if __name__ == '__main__':
  i = IRCClient()
  i.connect('irc.betainstitute.org', 6667)
