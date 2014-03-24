import re
import urllib2
import HTMLParser
import pickle

class PageTitle():
    def __init__(self, irc, plugins):
        self.plugins = plugins
        self.irc = irc
        self.irc.on_privmsg += self.check_for_url

    def shutdown(self):
        self.irc.on_privmsg -= self.check_for_url

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

    def check_for_url(self, destination, nick, user, host, message):
        m = re.search("https?\://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,4}(/\S*)?", message)
        if m is not None:
            url = m.group()
            r = urllib2.Request(url=url)
            f = urllib2.urlopen(r)
            contents = f.read()
            t = re.search("<title>(.+?)</title>", contents, re.DOTALL)
            real_url = f.geturl()
            real_host = re.search("https?://([^/\?]+)/?", real_url).group(1)

            h = HTMLParser.HTMLParser()

            # Special handlers
            if 'youtube.com' in real_url and 'watch' in real_url:
                title = h.unescape(t.group(1).replace(' - YouTube', '')).encode('utf-8')
                views = re.sub('\s', '', re.search("watch-view-count[^>]+?>(.*?)</span>", contents, re.DOTALL).group(1)).replace("views", "")
                likes = re.search("likes-count\">(.*?)</span>", contents, re.DOTALL).group(1)
                dislikes = re.search("dislikes-count\">(.*?)</span>", contents, re.DOTALL).group(1)
                self.irc.privmsg(destination, self.color("{bold}[{black},{white}]You[{white},{red}]Tube{reset} %s{bold} {bold}[{bold}[{green}]{bold}{bold}%s{reset} views{bold}]{bold} {bold}[{bold}[{green}]{bold}{bold}%s{reset} likes, [{green}]{bold}{bold}%s{reset} dislikes{bold}]{bold}" %
                                              (title, views, likes, dislikes)))
            elif 'twitter.com' in real_url and 'status' in real_url:
                #self.irc.privmsg(destination, 'Twitter')
                tweet = re.search("js-tweet-text tweet-text[^>]+?>(.*?)</p>", contents, re.DOTALL).group(1)
                tweet = re.sub('<[^<]+?>', '', tweet)
                #self.irc.privmsg(destination, "Tweet before encoding: %r" % tweet)
                #self.irc.privmsg(destination, "Pickled: %r" % pickle.dumps(tweet))
                try:
                    #tweet = ''.join(unichr(ord(x)) for x in tweet).encode('utf-8')
                    tweet = unicode(tweet.decode('utf-8')).encode('utf-8')
                except Exception, e:
                    self.irc.privmsg(destination, "Exception during Unicode encode: %s" % e)
                #self.irc.privmsg(destination, 'Past encode.')
                try:
                    retweets = re.search("Retweeted\s(.*?)\stime", contents, re.DOTALL).group(1)
                except:
                    retweets = '0'
                #self.irc.privmsg(destination, 'Past retweet.')
                try:
                    favorites = re.search("Favorited\s(.*?)\stime", contents, re.DOTALL).group(1)
                except:
                    favorites = '0'
                #self.irc.privmsg(destination, 'Past favorite.')
                self.irc.privmsg(destination, self.color("[{blue}]Twitter{reset}: [%s retweets] [%s favorites] %s" %
                                                         (retweets, favorites, tweet)))
            else:
                if t is not None:
                    ptitle = ' '.join(t.group(1).split('\n')).lstrip().rstrip()
                    try:
                        self.irc.privmsg(destination, self.color("{bold}[{bold}[{green}]%s{reset}{bold}] %s{bold}" %
                                                                (real_host, ptitle)))
                    except Exception, e:
                        self.irc.privmsg(destination, "Exception getting title: %s" % e)
                else:
                    self.irc.privmsg(destination, self.color("{bold}[{bold}[{green}]%s{reset}{bold}] No title{bold}" %
                                                             real_host))

def initialize(irc, plugins):
    try:
        global page_title
        page_title = PageTitle(irc, plugins)
        return True
    except Exception, e:
        irc.set_exception(e)
        return False

def shutdown():
    global page_title
    page_title.shutdown()
    return True
