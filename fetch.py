import requests
import config
import re

class Fetch:
    def fetch_nodes(self, client):
        print(f"\n\t... Obtaining nodes ...\n")
        try:
            response = client.session.get(config.DOWN_NODE_URL, timeout=config.TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch nodes: {e}")
            return None

    def fetch_interfaces(self, client):
        print(f"\n\t... Obtaining interfaces ...\n")
        try:
            response = client.session.get(config.DOWN_INTERFACES_URL, timeout=config.TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch interfaces: {e}")
            return None

    def fetch_downtime(self, client, item):
        """Visits individual detail page to extract exact timestamp."""
        try:
            response = client.session.get(item['url'], timeout=config.TIMEOUT)
            response.raise_for_status()
            
            # Look for timestamp signatures like 29-Jul-26 10:16 AM
            match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{2,4}\s+\d{1,2}:\d{2}(?:\s*[AM|PM]+)?)', response.text, re.IGNORECASE)
            return match.group(1) if match else "Time Unknown"
        except Exception:
            return "Fetch Error"