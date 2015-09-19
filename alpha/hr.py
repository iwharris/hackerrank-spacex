from requests import Session
import requests

HR_URL = "https://www.hackerrank.com" # Base URL for all requests to hackerrank

URL_LOGIN = HR_URL + "/users/sign_in.json"
URL_LOGOUT = HR_URL + "/users/sign_out?remote=true&commit=Sign+out&utf8=%E2%9C%93"
URL_STATS = HR_URL + "/splash/userstats.json"
URL_LEADERBOARD = HR_URL + "/splash/leaderboard.json"
URL_CHALLENGE = HR_URL + "/splash/challenge.json"

STATUS_OK = 200

class HRSession(Session):
    
    myHeaders = {
        'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
        'Connection' : 'keep-alive'
    }
    
    def __init__(self, *args, **kwargs):
        super(HRSession, self).__init__(*args, **kwargs)
        self.headers = self.myHeaders
        self.requests = requests.session(headers=self.headers)
        self.wait_time = 10
        
    # Attempts to log in with the given username and password. 
    # Authentication failure results in an exception being thrown.
    def login(self,username,password):
        response = self.post(URL_LOGIN, data = {
            'commit' : 'Sign in',
            'user[remember_me]' : '1',
            'user[login]' : username,
            'user[password]' : password,
            'remote' : 'true',
        }, headers=self.headers)
        if 'error' in response.json:
            raise Exception("ERROR: '%s'" % (response.json['error']))
        for k in response.cookies.keys(): 
            self.cookies[k] = response.cookies[k] # Store session cookies
        return response.json
        
    # Logs out of the current session. Returns True if successful, False otherwise.
    def logout(self):
        response = self.get(URL_LOGOUT)
        self.cookies = {}
        self.headers = self.myHeaders
        return response.status_code == STATUS_OK

    # Gets stats for the current user.
    def get_stats(self):
        return self.get(URL_STATS).json

    # Retrieves the leaderboard in JSON format.
    def get_leaderboard(self):
        return self.get(URL_LEADERBOARD).json
        
    def hrpost(self,url,data):
        return self.post(url, data)
        
    def hrget(self,url):
        return self.get(url)
