import os
import os.path
import sys
import time
import urllib.parse as up
import requests
import json

from shutil import which
from selenium import webdriver
from selenium.webdriver.common.by import By

CLIENT_ID = "{0}@AMER.OAUTHAP"
AUTH_URL  = "https://auth.tdameritrade.com/auth?response_type=code&redirect_uri={0}&client_id={1}"

def get_chrome_location():
    if sys.platform == 'darwin':
        # MacOS
        if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif os.path.exists("/Applications/Chrome.app/Contents/MacOS/Google Chrome"):
            return "/Applications/Chrome.app/Contents/MacOS/Google Chrome"
    elif 'linux' in sys.platform:
        # Linux
        return which('google-chrome') or which('chrome') or which('chromium')

    else:
        # Windows
        if os.path.exists('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'):
            return 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
        elif os.path.exists('C:/Program Files/Google/Chrome/Application/chrome.exe'):
            return 'C:/Program Files/Google/Chrome/Application/chrome.exe'

def fetch_selenium_driver():

    options = webdriver.ChromeOptions()
    options.binary_location = get_chrome_location()
    chrome_driver_binary = which('chromedriver') or "/usr/local/bin/chromedriver"
    driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)

    return driver

def initialize(
    client_id, 
    redirect_uri, 
    username=None, 
    password=None):

    global CLIENT_ID, AUTH_URL
    CLIENT_ID = CLIENT_ID.format(client_id)
    AUTH_URL  = AUTH_URL.format(up.quote(redirect_uri) , up.quote(CLIENT_ID))

    driver = fetch_selenium_driver() 
    driver.get(AUTH_URL)

    if username and password:
        ubox = driver.find_element(By.NAME, 'su_username')
        pbox = driver.find_element(By.NAME, 'su_password')
        ubox.send_keys(username)
        pbox.send_keys(password)
        driver.find_element(By.NAME, 'authorize').click()

        while True:
            try:
                code = up.unquote(driver.current_url.split('code=')[1])
                if code != '':
                    break
                else:
                    time.sleep(5)
            except (TypeError, IndexError):
                pass
    else:
        # Wait until the current URL starts with the callback URL
        # Tolerate redirects to HTTPS on the callback URL
        redirect_url = redirect_uri
        if redirect_url.startswith('http://'):
            print(('WARNING: Your redirect URL ({}) will transmit data over HTTP, ' +
                    'which is a potentially severe security vulnerability. ' +
                    'Please go to your app\'s configuration with TDAmeritrade ' +
                    'and update your redirect URL to begin with \'https\' ' +
                    'to stop seeing this message.').format(redirect_url))

            redirect_urls = (redirect_url, 'https' + redirect_url[4:])
        else:
            redirect_urls = (redirect_url,)
        current_url = ''
        num_waits = 0
        while not any(current_url.startswith(r_url) for r_url in redirect_urls):
            current_url = driver.current_url

            if num_waits > 3000:
                raise RedirectTimeoutError('timed out waiting for redirect')
            time.sleep(0.1)
            num_waits += 1

        code = up.unquote(driver.current_url.split('code=')[1])

    driver.close()

    resp = requests.post(
        url    ='https://api.tdameritrade.com/v1/oauth2/token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data   ={
                'grant_type': 'authorization_code',
                'refresh_token': '',
                'access_type': 'offline',
                'code': code,
                'client_id': client_id,
                'redirect_uri': redirect_uri
    })

    if resp.status_code != 200:
        return { 
            "error" : f"[{resp.status_code}] Could not authenticate",
            "msg"   : f"{resp.text}"
        }

    with open('td_credentials.json', 'w') as f:
        json.dump(resp.json(), f, indent=4)



def refresh(refresh_token, client_id):

    resp = requests.post(
        'https://api.tdameritrade.com/v1/oauth2/token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id
        })
    
    if resp.status_code != 200:
        return { 
            "error" : f"[{resp.status_code}] Could not authenticate",
            "msg"   : f"{resp.text}"
        }

    return resp.json()


