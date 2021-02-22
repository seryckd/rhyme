import sys
import requests
import json
import re
from bs4 import BeautifulSoup

def output(word, entry, data):
    if (data == None):
        data = ''
    o = word + ', ' + entry + ', ' + data
    print(o, flush=True)

def scrape(session, word, history):

    if (word in history):
        return

    history.append(word)

    url = 'https://dictionary.cambridge.org/dictionary/english/' + word

    response = session.get(url,  
        allow_redirects=True, 
        headers={ 
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15"
            })

    # Has the request for a word been referred to another word
    # https://dictionary.cambridge.org/dictionary/english/abate?q=abates
    m = re.match(r'.*/(?P<root>[a-z-]*)\?q=(?P<word>[a-z]*)', response.url)

    if m:
        # Yes. Note that the asked for word has been referred to the new word
        output(word, 'REF', m.group('root'))
        # and then continue with the referred word
        word = m.group('root')

    soup = BeautifulSoup(response.text, "html.parser")

    # The words are under 'dictionary'
    dictionary = soup.find('div', class_='dictionary')
    
    if (dictionary == None):
        # the word is not available
        output(word, 'NA', 'Not in dictionary')
        return

    body = dictionary.find('div', class_='di-body')
    entries = body.find_all('div', class_='entry')

    # Some words have multiple entries, like 'tear', or 'lead'
    for entry in entries:

        # Some entries link to other words.  'Abased' -> 'Abase'

        # <a class="Ref" href="/dictionary/english/abase" title="meaning of abase">
        #   <span class="x-h dx-h">abase</span>
        # </a>
        ref = entry.find('a', class_="Ref")
        if (ref != None):
            m = re.match(r'.*/(?P<ref>.*)$', ref['href'])
            ref_word = m.group('ref')
            output(word, 'REF', ref_word)
            scrape(session, ref_word, history)

        # There are also US prononciations, maybe later
        ukprons = entry.find('span', class_="uk dpron-i")
        
        if (ukprons == None):
            if (ref == None):
                # If there is no reference and no pronounication
                output(word, 'NA', 'No UK prononciation')
            return

        # The pronciation is something like this
        # <span class="pron dpron">/<span class="ipa dipa lpr-2 lpl-1">ˈæk.tə<span class="sp dsp">r</span></span>/</span>

        # It can also be
        # <span class="pron dpron">/<span class="ipa dipa lpr-2 lpl-1">ˈæb.ə.twɑː<span class="sp dsp">r</span></span>/</span>
        # <span class="pron dpron"><span class="lab dlab">strong</span> /<span class="ipa dipa lpr-2 lpl-1">biː</span>/</span>
        prons = ukprons.find('span', class_='dpron')

        # It's also possible to have the spoken prononciation but no phonetics
        if (prons == None):
            output(word, 'NA', 'No UK phonetics')
            return

        ipa = prons.find('span', class_='ipa')
        output(word, 'UKPRON', ipa.text)

def tryall(startFrom=''):
    with open('../data/corncob.js', 'r') as myfile:
        obj = json.load(myfile)

    go = False

    if (startFrom == ''):
        go = True

    with requests.Session() as session:
        for o in obj:

            if (go):
                scrape(session, o, [])

            elif (o == startFrom):
                go = True


#out = open("myfile.txt", "w", encoding="utf-8")

# Examples

# typical
#scrape(requests, 'actor', [])

# Refers to another word
#scrape(requests, 'abased', [])

# Refers to another word and has the pronunication
#scrape(requests, 'am', [])

# Does not exist
#scrape(requests, 'aardwolf', [])

# Muliple entries/prononciation
#scrape(requests, 'tear', [])
#scrape(requests, 'lead', [])

# searching for 'abides' refers to a root word (/abide?q=abides)
#scrape(requests, 'abides', [])

# sometimes parts of the pronunication are in superscript (like the final r)
# <span class="ipa dipa lpr-2 lpl-1">ˈæb.ə.twɑː<span class="sp dsp">r</span></span>
#scrape(requests, 'abattoir', [])

# US only word
#scrape(requests, 'academics', [])

# Had a problem with enumerating of the children of 'di-body'
#scrape(requests, 'accede', [])

# Refers to a word with no spoken pronunication
#scrape(requests, 'actualisation', [])

#scrape(requests, 'aspersions', [])

# TODO - has /strong/ and /weak/ variations which I am not capturing
#scrape(requests, 'be', [])

# Loops: 'brahman' -> 'brahim' -> 'brahman'
scrape(requests, 'brahman', [])

# Refers to a link with numbers 'ftse-100' 
#scrape(requests, 'footsie', [])

#scrape(requests, 'hoarded', [])

#tryall('unisex')

