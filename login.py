# login.py
import requests
from bs4 import BeautifulSoup
import config

class OrionClient:
    def __init__(self):
        self.session = requests.Session()
    

    def authenticate(self):
        print("[*] Initiating connection to SolarWinds...")
        try:
            # 1. Grab initial page to get ViewState tokens
            response = self.session.get(config.LOGIN_URL, timeout=config.TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            viewstate = soup.find('input', {'id': '__VIEWSTATE'})
            eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})

            # 2. Build the payload
            payload = {
                '__VIEWSTATE': viewstate['value'] if viewstate else "",
                '__EVENTVALIDATION': eventvalidation['value'] if eventvalidation else "",
                'ctl00$ContentPlaceHolder1$Username': config.USERNAME,
                'ctl00$ContentPlaceHolder1$Password': config.PASSWORD,
                'ctl00$ContentPlaceHolder1$LoginButton.x': '1',
                'ctl00$ContentPlaceHolder1$LoginButton.y': '1'
            }

            # 3. Post credentials exactly as your test script did (default redirects)
            self.session.post(config.LOGIN_URL, data=payload, timeout=config.TIMEOUT)
            
            print("[+] Authentication POST completed.")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[-] Network Error during authentication: {e}")
            return False

