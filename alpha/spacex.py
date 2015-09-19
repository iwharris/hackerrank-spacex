# -*- coding: utf-8 -*-

import hr
import json
import sys
import logging
import datetime
import string
import base64
from bs4 import BeautifulSoup
import re

# Requires beautifulsoup4, get using pip install beautifulsoup4

alphabet = [chr(a) for a in range(ord('a'),ord('z')+1)]

numvalues = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, \
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, \
    'twenty': 20, 'thirty': 30, 'fourty': 40, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90
}

class HRSpaceSession(hr.HRSession):
    
    URL_SPACECHALLENGE = hr.HR_URL + '/game.json'
    
    wikipages = {}
    
    logger = None
    
    def __init__(self):
        super(HRSpaceSession, self).__init__()              
        logging.basicConfig(
            filename='spacex.log',
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger('hr')
        self.logger.info("Beginning SpaceX solver at %s", (str(datetime.datetime.now())))
        consoleLogger = logging.StreamHandler()
        consoleLogger.setLevel(logging.INFO)
        self.logger.addHandler(consoleLogger)

    # Rotates a single char
    def rotateChar(self,c,rotation):
        global alphabet
        if c in alphabet:
            i = alphabet.index(c) + rotation
            if i >= len(alphabet):
                i -= len(alphabet)
            return alphabet[i]
        elif c.lower() in alphabet:
            #print self.rotateChar(c.lower(),rotation).upper()
            return self.rotateChar(c.lower(),rotation).upper()
        else: # non-alphabetic characters don't need decryption
            return c

    # Rotates the given string using the given offset
    def decrypt(self,estring,rotation):
        #print ''.join([self.rotateChar(c,rotation) for c in estring])
        return ''.join([self.rotateChar(c,rotation) for c in estring])

    # Attempts to find the offset for rotation between a start string and a destination string.
    # Returns rotation offset as a positive integer in the domain [0,25].
    # Throws exceptions if an error occurs (length mismatch, inconsistent offset).
    def findRotation(self,estring,dstring):
        global alphabet
        if len(estring) == len(dstring):
            estring = estring.lower()
            dstring = dstring.lower()
            prev = 0    
            for i in range(0,len(estring)):
                c = estring[i]
                if c in alphabet:
                    d = ord(dstring[i]) - ord(estring[i])
                    if d < 0:
                        d += len(alphabet)
                    elif d >= len(alphabet):
                        d -= len(alphabet)
                    if (i > 0) and (d != prev):
                        raise Exception("Offset mismatch")
                    else:
                        prev = d
                    return prev
        else:
            raise Exception("Length mismatch")

    def parseNumStr(self,numstr):
        global numvalues
        tokens = numstr.lower().replace('-',' ').replace(',',' ').split()
        a = 0
        for t in tokens:
            if t in numvalues:
                a += numvalues[t]
            elif t == 'thousand':
                a *= 1000
            elif t == 'hundred':
                a = ((a % 10) * 100) + ((a / 10) * 10) # Take the ones position and move it to hundreds
            elif t == 'and':
                continue
            else:
                raise Exception("String '%s' does not parse!" % (t))
        return a
        
    # Tries to solve an easy game (n <= 10000)
    def solveEasyGame(self,numString):
        global alphabet
        numString = numString.lower()
        for i in range(len(alphabet)):
            try:
                result = self.parseNumStr(self.decrypt(numString,i)) # Try different offsets and then see if the decrypted result parses as a number
                return result
            except Exception:
                continue
        raise Exception("Did not find a solution for string '%s'!" % (numString))
        
    # Tries to solve a hard game (10000 < n <= 11000)
    # Returns the 
    def solveHardGame(self,sampleQuestion,sampleAnswer,sources,cphQuestion):
        src = [base64.b64decode(string.join(string.split(s,'\n'))) for s in sources] # Get URLs of wiki sources
        #wiki = [self.getWikiContents(s) for s in src] # Get contents of wiki sources
        # Generate a "rainbow table" of all different decryptions of the sample answer
        decryptions = [self.decrypt(sampleAnswer,i) for i in range(len(alphabet))]
        # For each element in the rainbow table, search through the contents of each URL for matches        
        for s in src:
            wiki = self.getWikiContents(s)
            for i in range(len(decryptions)):
                if string.find(wiki,decryptions[i]) >= 0:
                    self.logger.debug("Found instance of '%s'! Rotation index is %d." % (decryptions[i],i))
                    r = re.search("'([^']*)'",self.decrypt(cphQuestion,i)).group(1)
                    return r.strip("'")
        raise Exception("Found no matches for string '%s' in %d different sources!" % (cphQuestion,len(src)))

    # Retrieves and cleans the content of a wiki page, only returning the human-readable text within the contents       
    def getWikiContents(self,wikiURL):
        try:
            return self.wikipages[wikiURL]
        except KeyError as e:
            response = self.get(wikiURL).text
            soup = BeautifulSoup(response)
            self.wikipages[wikiURL] = soup.find(id="mw-content-text").get_text().lower()
            return self.wikipages[wikiURL]

    # Retrieves the game json data from scientist n.
    def getgameinfo(self,n):
        response = self.post(self.URL_SPACECHALLENGE, data = {
            'n' : n,
            'remote' : 'true'
        },headers=self.headers,cookies=self.cookies)
        #print response.json['game']
        if response.ok and (response.json['ok']):
            return response.json['game']
        elif response.json['message']:
            raise Exception("Error: %s" % (response.json[message]))
        raise Exception("Error: API call failed!")

    # Submits the solution for a given game id. 
    # Solution is the 4-digit number in integer form.
    def hr_solvegame(self,idnum,n,solution):
        return self.put(self.URL_SPACECHALLENGE, data = {
            'id' : idnum,
            'answer' : solution,
            'remote' : 'true'
        })

    # Autosolves the scientist n.
    # Retrieves challenge information, finds a decrypted solution, and submits it to server
    def autosolve(self,n):
        global alphabet
        try:
            r = self.getgameinfo(n)
        except Exception as e:
            self.logger.warn("Could not get game info for n=%d. Message: '%s'" % (n,e))
            return False,e,0
        solution = 0
        idnum = int(r['id'])
        # Branch based on the question type
        if n <= 10000:
            estring = r['cph_number'].strip()
            try:
                solution = self.solveEasyGame(estring)
            except Exception as e:
                self.logger.warn("Could not solve n=%d. Message: '%s'" % (n,e))
                return False,estring,'0'            
        elif n > 10000 and n <= 11000:
            sample_question = r['sample_question']
            sample_answer_cph = r['sample_cph_answer'].lower()
            source = r['source']
            cph_question = r['cph_question']
            try:
                solution = self.solveHardGame(sample_question,sample_answer_cph,source,cph_question)
            except Exception as e:
                self.logger.warn("Could not solve n=%d with question '"'%s'"'. Message: '%s'" % (n,cph_question,e))
                return False,sample_answer_cph,cph_question
        elif n > 11000:
            return False,'',0
        #print idnum,n,solution
        r = self.hr_solvegame(idnum,n,solution)
        #print r
        #print r.json
        if r.json['exit'] == 0:
            return True,idnum,solution
        else:
            return False,idnum,"Reason: '%s', Attempted solution was '%s'" % (r.json['message'],solution)
        #return (True if r.json['exit'] == 0 else False),idnum,solution
            
# Runs for scientists n (inclusive), start <= n <= end
def main(username,password,start=1,end=11100):
    session = HRSpaceSession()
    session.logger.info("Logging in as '%s'..." % (username))
    try:
        session.login(username,password)
    except Exception as e:
        session.logger.error(e)
        exit()
    session.logger.info("Login successful.")
    stats = session.get_stats()
    session.logger.info("The stats for username '%s': %d points, rank %d" % (stats['user'],stats['score'],stats['rank']))
    session.logger.info("Solving for scientists from %d to %d..." % (start,end))
    cnt_solved = 0
    cnt_failed = 0
    cnt_total = end - start + 1
    for n in range(start,end+1):
        result,estring,solution = session.autosolve(n)
        if result:
            session.logger.info("Solved scientist %d: '%s' => %s" % (n,estring,solution))
            cnt_solved += 1
        else:
            session.logger.warn("Couldn't solve scientist %d: '%s'!" % (n,solution))
            cnt_failed += 1
    session.logger.info("Finished autosolving.")
    session.logger.info("\nSolved: %d/%d (%d%%)     Failed: %d/%d (%d%%)" % (cnt_solved,cnt_total,(cnt_solved/cnt_total) * 100,cnt_failed,cnt_total,(cnt_failed/cnt_total) * 100))
    stats = session.get_stats()
    session.logger.info("New stats for '%s': %d points, rank %d" % (stats['user'],stats['score'],stats['rank']))
    session.logger.info("Logging out.")
    try:
        session.logout()
    except:
        pass    
    
main('email','password',1,11000)    
