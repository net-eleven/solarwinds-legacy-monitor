import requests
import config


class Fetch:
    def __init__(self):
        self.session = requests.Session()

    def fetch_nodes(self):
        print(f"[*] Fetching nodes from {config.DOWN_NODE_URL} ...")
        try:
            response = self.session.get(config.DOWN_NODE_URL, timeout=config.TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch nodes: {e}")
            return None


    def fetch_interfaces(self):
        print(f"[*] Fetching interfaces from {config.DOWN_INTERFACES_URL} ...")
        try:
            response = self.session.get(config.DOWN_INTERFACES_URL, timeout=config.TIMEOUT)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch interfaces: {e}")
            return None
