import socket

BUFFER_SIZE = 1024

class SimpleTCPClient(object):
  def __init__(self):
    pass

  def on_connected(self):
    pass

  def on_disconnected(self):
    pass

  def on_error(self, exception):
    pass

  def on_recv(self, data):
    pass

  def connect(self, host, port):
    try:
      self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except IOError as e:
      self.on_error(e)
    try:
      self.s.connect((host, port))
      self.on_connected(host, port)
      self.loop()
    except IOError as e:
      self.on_error(e)
      self.s.close()

  def push(self, data):
    try:
      self.s.send(data)
    except IOError as e:
      self.on_error(e)
      self.s.close()

  def loop(self):
    while True:
      data = self.s.recv(BUFFER_SIZE)
      if len(data) == 0:
        self.on_disconnected()
        self.s.close()
        break
      else:
        self.on_recv(data)

