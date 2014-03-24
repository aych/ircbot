import urllib2
import re
import HTMLParser


class Lyrics():
    def __init__(self, irc, plugins):
        self.plugins = plugins
        self.irc = irc
        self.irc.on_command += self.handle_command

    def shutdown(self):
        self.irc.on_command -= self.handle_command

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

    def handle_command(self, destination, nick, user, host, command, params):
        if command == "LYRICBOT":
            get_lyrics()

def get_lyrics():
    r = urllib2.Request(url='http://lyrics.wikia.com/Special:Random')
    f = urllib2.urlopen(r)
    contents = f.read()
    song = re.search("<title>(.+?)</title>", contents, re.DOTALL)
    song = song.group(1).replace(' - Lyric Wiki - song lyrics, music lyrics', '')
    if song.endswith(' Lyrics'):
        song = song[:-7]
    if song.startswith('LyricFind:'):
        song = song[10:]

    artist = song.split(':')[0]
    song = song.split(':')[1]

    print artist, song

    h = HTMLParser.HTMLParser()

def initialize(irc, plugins):
    try:
        global lyrics
        lyrics = Lyrics(irc, plugins)
        return True
    except Exception, e:
        irc.set_exception(e)
        return False

def shutdown():
    global lyrics
    lyrics.shutdown()
    return True

if __name__ == '__main__':
    get_lyrics()