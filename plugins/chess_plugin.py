import re
import chess

PLUGIN_CLASS = 'ChessGame'

class ChessGame(object):
    def __init__(self, irc):
        self.plugins = irc.plugins
        self.irc = irc
        self.irc.on_command += self.irc_command
        self.game_running = False
        self.board = None
        self.player_white = ''
        self.player_black = ''
        self.board_white = 'gray'
        self.board_black = 'black'
        self.piece_white = 'orange'
        self.piece_black = 'green'
        self.color_last_move = 'darkblue'

    def shutdown(self):
        self.irc.on_command -= self.irc_command
        return True

    def dependency_loaded(self, module):
        if module in self.plugins:
            return True
        else:
            return False

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

    def render_square(self, white, piece, last_move=False):
      buf = ''
      if piece.isupper():
        piece_color = self.piece_white
      else:
        piece_color = self.piece_black
      if last_move:
        buf += '[{%s},{%s}]' % (piece_color, self.color_last_move)
      elif white:
        buf += '[{%s},{%s}]' % (piece_color, self.board_white)
      else:
        buf += '[{%s},{%s}]' % (piece_color, self.board_black)
      buf += ' %s ' % piece
      return buf

    def print_board(self, destination, move=[]):
      parts = self.board.fen.split(' ')
      board = parts[0].split('/')

      white = False
      self.irc.privmsg(destination, '    a  b  c  d  e  f  g  h')
      row = 8
      for l in board:
        col = 1
        buf = ' %d ' % row
        white = not white
        for c in l:
          if c.isdigit():
            for i in range(0, int(c)):
              cell = chr(ord('a')-1 + col) + str(row)
              buf += self.render_square(white, ' ', cell in move)
              col += 1
              white = not white
          else:
            cell = chr(ord('a')-1 + col) + str(row)
            buf += self.render_square(white, c, cell in move)
            col += 1
            white = not white
        buf += '{reset} %d' % row
        row -= 1
        self.irc.privmsg(destination, self.color(buf))
      self.irc.privmsg(destination, '    a  b  c  d  e  f  g  h')

    def end_game(self):
      self.game_running = False
      self.player_white = ''
      self.player_black = ''
      self.last_move = ''
      self.board = None

    def eval_move(self, destination, move):
      try:
        if not chess.Move.from_uci(move) in self.board.get_legal_moves():
          self.irc.privmsg(destination, "That move is not legal.")
        else:
          self.board.make_move(chess.Move.from_uci(move))
          self.print_board(destination, move)
          if self.board.is_stalemate():
            self.irc.privmsg(destination, "The game is a stalemate.")
            self.end_game()
          elif self.board.is_insufficient_material():
            self.irc.privmsg(destination, "The game is drawn due to insufficient material.")
            self.end_game()
          elif self.board.is_game_over():
            self.irc.privmsg(destination, "Checkmate!")
            self.end_game()
          elif self.board.is_check():
            self.irc.privmsg(destination, "Check!")
      except Exception, e:
        self.irc.privmsg(destination, "Could not parse move, try again.")

    def whose_turn(self):
      return self.board.fen.split(' ')[1]

    def irc_command(self, destination, nick, user, host, command, params):
      if command == 'CHESS.BEGIN' and self.game_running == False and self.board is None:
        self.board = chess.Position()
        self.irc.privmsg(destination, 'A chess game has been started, use chess.join to sit.')
      elif command == 'CHESS.JOIN' and self.game_running == False and self.board is not None:
        if self.player_white == '':
          self.player_white = nick
        elif self.player_black == '':
          self.player_black = nick
          self.irc.privmsg(destination, 'Players joined: %s (white) and %s (black)' % (self.player_white, self.player_black))
          self.game_running = True
          self.print_board(destination)
      elif command == 'CHESS.BOARD' and self.game_running == True:
        self.print_board(destination)
      elif command == 'CHESS.MOVE':
        if self.game_running == True and len(params) > 1:
          if (self.whose_turn() == 'w' and self.player_white == nick) or (self.whose_turn() == 'b' and self.player_black == nick):
            self.eval_move(destination, params[1])
      elif command == 'CHESS.COLOR' and nick == 'rife':
        if params[1] == 'board.white':
          self.board_white = params[2]
        elif params[1] == 'board.black':
          self.board_black = params[2]
        elif params[1] == 'pieces.white':
          self.piece_white = params[2]
        elif params[1] == 'pieces.black':
          self.piece_black = params[2]
        elif params[1] == 'last.move':
          self.color_last_move = params[2]
      elif command == 'CHESS.RESET':
        if self.game_running == True and (self.player_white == nick or self.player_black == nick):
          self.end_game()
          self.irc.privmsg(destination, "Game ended by %s." % nick)
