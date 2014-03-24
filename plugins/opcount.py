import pickle
import re

class OpCount():
    def __init__(self, irc, plugins):
        self.irc = irc
        self.plugins = plugins
        self.irc.on_mode_change += self.irc_mode_change
        self.irc.on_command += self.irc_command
        self.op_table = {}

        # Unpickle the auth list.
        try:
            self.op_table = pickle.load(open('plugins/data/op_table.pkl', 'rb'))
        except Exception, e:
            # First time run, create the auth file.
            pickle.dump(self.op_table, open('plugins/data/op_table.pkl', 'wb'))

    def shutdown(self):
        pickle.dump(self.op_table, open('plugins/data/op_table.pkl', 'wb'))
        self.irc.on_mode_change -= self.irc_mode_change
        self.irc.on_command -= self.irc_command

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

    def irc_command(self, destination, nick, user, host, command, params):
        if command == 'OPS.LEADERS':
            if destination in self.op_table:
                chan_table = self.op_table[destination]

                # Build a sorted table, I guess?
                d = {}
                for n in chan_table.keys():
                    d[n] = 0
                    if '+o' in chan_table[n]:
                        d[n] = chan_table[n]['+o']
                    else:
                        chan_table[n]['+o'] = 0
                    if '-o' in chan_table[n]:
                        d[n] -= chan_table[n]['-o']
                    else:
                        chan_table[n]['-o'] = 0

                for x in sorted(d, key=d.get, reverse=True)[:3]:
                    self.irc.privmsg(destination, self.color("%s: {bold}[{bold}[{green}]+%d{reset}{bold}]{bold} {bold}[{bold}[{red}]-%d{reset}{bold}]{bold} = [{blue}]%d{reset}") % (x, chan_table[x]['+o'], chan_table[x]['-o'], d[x]))

    def irc_mode_change(self, nick, user, host, destination, modes):
        mode_params = modes.split(' ')
        if destination[0] == '#' and len(mode_params) > 1:
            chan_ops = {}
            if destination in self.op_table:
                chan_ops = self.op_table[destination]
            else:
                self.op_table[destination] = chan_ops

            nick_table = {}
            if nick in chan_ops:
                nick_table = chan_ops[nick]
            else:
                chan_ops[nick] = nick_table

            # Parse the modes
            mode_add = False
            flag = '-'
            index = 0
            op_count = 0
            for m in mode_params[0]:
                if m == '+':
                    mode_add = True
                    flag = '+'
                elif m == '-':
                    mode_add = False
                    flag = '-'
                else:
                    index += 1
                    if "%s%s" % (flag, m) not in nick_table:
                        nick_table[flag + m] = 0

                    nick_table[flag + m] += 1

                    if flag + m == '+o':
                        op_count += 1

            pickle.dump(self.op_table, open('plugins/data/op_table.pkl', 'wb'))

            #if op_count == 3:
                #self.irc.privmsg(destination,
                #                 self.color("[{yellow}]{bold}+3{bold}{reset} [{green}]%s{reset} scores a hat trick [{yellow}]{bold}+3{bold}" % nick))

def initialize(irc, plugins):
    global t
    t = OpCount(irc, plugins)
    return True

def get_instance():
    global t
    return t

def shutdown():
    global t
    t.shutdown()
    return True