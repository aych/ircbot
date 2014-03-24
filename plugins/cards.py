import re
import threading
import random
import collections

PHASE_GO = 0
PHASE_JOIN = 1
PHASE_PREGAME = 2
PHASE_BEGIN_TURN = 3
PHASE_PLAY = 4
PHASE_PREWINNER = 5
PHASE_WINNER = 6
PHASE_POSTWINNER = 7

PHASE_TICKS = {PHASE_GO: 2,
               PHASE_JOIN: 4,
               PHASE_PREGAME: 1,
               PHASE_BEGIN_TURN: 1,
               PHASE_PLAY: 120,
               PHASE_PREWINNER: 1,
               PHASE_WINNER: 60,
               PHASE_POSTWINNER: 1}
PHASE_DURATION = {PHASE_GO: 1.0,
                  PHASE_JOIN: 15.0,
                  PHASE_PREGAME: 1.0,
                  PHASE_BEGIN_TURN: 5.0,
                  PHASE_PLAY: 1.0,
                  PHASE_PREWINNER: 1.0,
                  PHASE_WINNER: 1.0,
                  PHASE_POSTWINNER: 1.0}

class Cards():
  def __init__(self, irc, plugins):
    self.irc = irc
    self.plugins = plugins
    self.irc.on_privmsg += self.on_privmsg
    self.timer = None
    self.channel = None
    self.phase = PHASE_GO
    self.players = []
    self.hands = {}
    self.tickcount = 1
    self.tick_duration = 1.0
    self.czar = None
    self.black_card = None
    self.blanks = 0
    self.can_play = []
    self.answers = {}
    self.shuffled_answers = {}
    self.complete_answers = {}
    self.points = {}
    self.czar = None
    self.white_set = []
    self.black_set = []
    self.play_to = 5
    self.load_cards()

  def load_cards(self):
    # Load the cards...
    with open('plugins/data/black_cards.txt') as f:
      self.black_set = f.readlines()
    with open('plugins/data/white_cards.txt') as f:
      self.white_set = f.readlines()

    print "Cards loaded!"

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

  def send_channel(self, text):
    if self.channel is not None:
      self.irc.privmsg(self.channel, self.color(text))

  def send_czar(self, text):
    if self.czar is not None:
      self.irc.notice(self.czar, self.color(text))

  def shutdown(self):
    self.irc.on_privmsg -= self.on_privmsg

  def on_privmsg(self, destination, nick, user, host, message):
    if message.startswith("cards.start"):
      if self.channel is None:
        self.channel = destination
      if self.timer is None:
        parts = message.split(' ')
        if len(parts) == 2:
          self.play_to = int(parts[1])
        self.channel = destination
        self.phase = PHASE_GO
        self.tickcount = PHASE_TICKS[PHASE_GO]
        self.on_tick()
      else:
        self.send_channel("{bold}[-]{bold} Game already in progress.")
    elif message == "cards.stop":
      if self.timer is not None:
        self.send_channel("{bold}[-]{bold} Game cancelled.")
        self.timer.cancel()
        self.timer = None
        self.game_over()
    elif self.phase == PHASE_JOIN and message == ".join":
      if nick not in self.players:
        self.players.append(nick)
        self.send_channel("{bold}[*]{bold} %s has joined the game." % nick)
    elif self.phase == PHASE_JOIN and message == ".forcejoin":
      self.players.append(nick)
    elif self.phase == PHASE_PLAY and message.startswith('.play'):
      if nick in self.can_play:
        pieces = message.split(' ')[1:]
        if len(pieces) != self.blanks:
          self.send_channel("{bold}[*]{bold} Sorry, %s, you didn't fill all of the blanks." % nick)
        else:
          fill_in = self.black_card
          tp = []
          for p in pieces:
            ix = int(p)-1
            if ix < len(self.hands[nick]):
              fill_in = fill_in.replace('_', self.hands[nick][ix], 1)
              tp.append(self.hands[nick][ix])
            else:
              return
          [self.hands[nick].remove(p) for p in tp]
          self.can_play.remove(nick)
          self.answers[nick] = pieces
          self.complete_answers[nick] = fill_in
          #self.send_czar("{bold}[*]{bold} %s answers: %s" % (nick, fill_in))
          if len(self.can_play) == 0:
            #for n in self.complete_answers:
            #  self.send_channel("{bold}[*]{bold} %s" % (self.complete_answers[n]))
            self.tickcount = 1
    elif self.phase == PHASE_WINNER:
      if nick != self.czar:
        return
      if not message.startswith('.winner'):
        return
      winner = message.split(' ')[1]

      print winner, self.shuffled_answers

      if winner in self.shuffled_answers:
        winner = self.shuffled_answers[winner]

      if winner.lower() in [p.lower() for p in self.players[1:]]:
        self.send_channel("{bold}[+]{bold} %s wins!" % winner)
        if winner in self.points:
          self.points[winner] += 1
        else:
          self.points[winner] = 1

        if self.points[winner] == self.play_to:
          send.send_channel("{bold}[+]{bold} The game is over, %s wins!" % winner)
          self.timer.cancel()
          self.timer = None
          self.game_over()
          return

        od = collections.OrderedDict(sorted(self.points.items(), key=lambda t: 0-t[1]))
        leaders = ''
        for i in range(0,3):
          if i < len(od):
            leaders += "%s: %d - " % (od.items()[i][0], od.items()[i][1])
        self.send_channel("{bold}[*]{bold} Leaders: %s" % leaders)

        self.new_hand()
      else:
        self.send_channel("{bold}[-]{bold} %s is not a valid player." % winner)

  def on_tick(self):
    if self.channel is None:
      self.game_over()
    self.tickcount -= 1
    if self.tickcount == 0:
      self.phase += 1
      self.tickcount = PHASE_TICKS[self.phase]
      self.tick_duration = PHASE_DURATION[self.phase]

    phases = {PHASE_GO: self.phase_go, PHASE_JOIN: self.phase_join, PHASE_PREGAME: self.phase_pregame,
              PHASE_BEGIN_TURN: self.phase_begin_turn, PHASE_PLAY: self.phase_play,
              PHASE_PREWINNER: self.phase_prewinner, PHASE_WINNER: self.phase_winner,
              PHASE_POSTWINNER: self.phase_postwinner}

    if self.phase in phases:
      phases[self.phase]()
    else:
      return

    self.timer = threading.Timer(self.tick_duration, self.on_tick)
    self.timer.start()

  def phase_go(self):
    self.send_channel("{bold}[*]{bold} A game has been started with [{white},{black}] %d black {reset} cards and [{black},{white}] %d white {reset} cards." % (len(self.black_set), len(self.white_set)))
    self.send_channel("{bold}[!]{bold} You will be playing first to {bold}%d{bold} points." % self.play_to)

  def phase_join(self):
    self.send_channel("{bold}[*]{bold} Now waiting for players to join... Type .join to play. Currently %d players: %s" % 
                    (len(self.players), ', '.join(self.players)))

  def phase_pregame(self):
    # Do we have enough players?
    if len(self.players) < 3:
      self.send_channel("{bold}[-]{bold} Too few players for a game, requires at least three.")
      self.timer = None
      self.game_over()
    self.black_cards = self.black_set
    self.white_cards = self.white_set

    # Shuffle stuff.
    random.shuffle(self.black_cards)
    random.shuffle(self.white_cards)
    random.shuffle(self.players)
    for p in self.players:
      self.hands[p] = []

  def phase_begin_turn(self):
    if len(self.players) < 3:
      return
    self.czar = self.players[0]
    self.can_play = self.players[1:]
    self.black_card = self.black_cards.pop().rstrip()
    self.blanks = self.black_card.count('_')
    self.send_channel("{bold}[*]{bold} Card Czar %s reads: %s" % (self.czar, self.black_card.replace('_','________')))
    self.send_channel("{bold}[*]{bold} Type: .play <card #> to fill in the blanks. Multiple cards are played with: .play <card #> <card #>")

    for i in range(1, 11):
      for p in self.can_play:
        if len(self.hands[p]) < 10:
          card = self.white_cards.pop().rstrip()
          self.hands[p].append(card)

    for p in self.can_play:
      hand = ""
      for i, c in enumerate(self.hands[p]):
        if i + 1 < len(self.hands[p]):
          hand += "%d: %s, " % (i + 1, c)
        else:
          hand += "%d, %s" % (i + 1, c)
      self.irc.notice(p, self.color("{bold}[*]{bold} Your hand is: [%s]" % hand))

  def phase_play(self):
    pass

  def phase_prewinner(self):
    if len(self.can_play) > 0:
      #self.send_channel("Play timeout expired, %s haven't played..." % self.can_play)
      for p in self.can_play:
        #self.send_channel("Iterating: %s" % p)
        pieces = []
        fill_in = self.black_card
        for i in range(0, self.blanks):
          pieces.append(self.hands[p][i])
          fill_in = fill_in.replace('_', self.hands[p][i], 1)
        for i in pieces:
          self.hands[p].remove(i)

        #self.send_channel("%s still haven't played..." % self.can_play)
        self.answers[p] = pieces
        self.complete_answers[p] = fill_in
        self.send_channel("{bold}[-]{bold} %s couldn't be bothered to play and sacrificed some cards: %s" % (p, fill_in))
      self.send_channel("{bold}[*]{bold} All players have played, the czar is picking a winner... Type: .winner <number>")
      self.can_play = []
    else:
      self.send_channel("{bold}[*]{bold} All players have turned in cards, the czar is picking a winner... Type: .winner <number>")

    shuffled = self.complete_answers.keys()
    random.shuffle(shuffled)
    self.shuffled_answers = {}
    for i, a in enumerate(shuffled):
      i += 1
      self.shuffled_answers[str(i)] = a
      self.send_channel("{bold}[Answer #%d]{bold} %s" % (i, self.complete_answers[a]))

  def phase_winner(self):
    pass

  def phase_postwinner(self):
    self.send_channel("{bold}[-]{bold} No winner was chosen, the card czar %s sucks." % self.czar)
    self.new_hand()

  def game_over(self):
    self.players = []
    self.points = {}
    self.answers = {}
    self.shuffled_answers = {}
    self.complete_answers = {}
    if self.timer is not None:
      self.timer.cancel()
    self.channel = None
    self.timer = None
    self.phase = PHASE_GO

  def new_hand(self):
    # Rotate the players and begin again.
    self.players = self.players[1:] + self.players[:1]
    self.phase = PHASE_PREGAME
    self.tickcount = 1
    self.shuffled_answers = {}
    self.complete_answers = {}
    self.timer.cancel()
    self.can_play = []
    self.answers = {}
    self.complete_answers = {}
    self.czar = None    
    self.on_tick()

def initialize(irc, plugins):
  global c
  c = Cards(irc, plugins)
  return True

def get_instance():
  global c
  return c

def shutdown():
  global c
  c.shutdown()
  return True
