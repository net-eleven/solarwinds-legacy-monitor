from datetime import datetime
import time
import openpyxl
from login import OrionClient
from fetch import Fetch
import parse

def parse_downtime_key(item):
    """Converts downtime string into a datetime object for sorting."""
    d_str = item.get('downtime', '')
    try:
        # Example format: '10-Aug-26 06:59 PM'
        return datetime.strptime(d_str, "%d-%b-%y %I:%M %p")
    except Exception:
        # Push unknown or unparseable dates to the bottom
        return datetime.min

def process_items_sequential(fetcher, client, items_list, delay=0.15):
    """Fetches downtime timestamps strictly one by one to avoid IIS session locking."""
    processed = []
    total = len(items_list)
    
    for idx, item in enumerate(items_list, start=1):
        downtime = fetcher.fetch_downtime(client, item)
        item['downtime'] = downtime
        
        if item['type'] == 'Interface':
            item['full_name'] = f"{item['parent']}-{item['name']}"
        else:
            item['full_name'] = item['name']
            
        item['display_str'] = f"[{downtime}] {item['full_name']}"
        processed.append(item)
        
        print(f"  [{idx}/{total}]  {downtime} - {item['full_name']}")
        time.sleep(delay)
        
    return processed

def main():
    print("=== NOC AUTOMATION START ===")

    client = OrionClient()
    if not client.authenticate():
        print("[-] Exiting due to authentication failure.")
        return

    fetcher = Fetch()

    # 1. Fetch & Parse DOWN NODES
    node_html = fetcher.fetch_nodes(client)
    raw_nodes = parse.parse_report_html(node_html, "Node") if node_html else []
    print(f"[*] Processing {len(raw_nodes)} Down Nodes sequentially...")
    down_nodes = process_items_sequential(fetcher, client, raw_nodes, delay=0.15)

    # 2. Fetch & Parse DOWN INTERFACES 
    interface_html = fetcher.fetch_interfaces(client)
    raw_interfaces = parse.parse_report_html(interface_html, "Interface") if interface_html else []
    print(f"[*] Processing {len(raw_interfaces)} Down Interfaces sequentially...")
    down_interfaces = process_items_sequential(fetcher, client, raw_interfaces, delay=0.15)

    # 3. Sort Most Recent First
    down_nodes.sort(key=parse_downtime_key, reverse=True)
    down_interfaces.sort(key=parse_downtime_key, reverse=True)

    # Re-build display strings after sorting to update output ordering cleanly
    node_text_lines = [f"[{n['downtime']}] {n['full_name']}" for n in down_nodes]
    interface_text_lines = [f"[{i['downtime']}] {i['full_name']}" for i in down_interfaces]

    # 4. Write text output (down.txt)
    with open("down.txt", "w", encoding="utf-8") as f:
        f.write("==== DOWN NODES (MOST RECENT FIRST) ====\n")
        f.write("\n".join(node_text_lines) + "\n\n\n")

        f.write("==== DOWN INTERFACES (MOST RECENT FIRST) ====\n")
        f.write("\n".join(interface_text_lines) + "\n")
    print("\n[+] Text report successfully saved to down.txt (sorted by timestamp)")

    # 5. Write Excel output (down_report.xlsx)
    wb = openpyxl.Workbook()
    
    # Sheet 1: Down Nodes
    ws_nodes = wb.active
    ws_nodes.title = "Down Nodes"
    ws_nodes.append(["Index", "Down Time", "Node Name"])
    for idx, item in enumerate(down_nodes, start=1):
        ws_nodes.append([idx, item['downtime'], item['name']])

    # Sheet 2: Down Interfaces
    ws_interfaces = wb.create_sheet(title="Down Interfaces")
    ws_interfaces.append(["Index", "Down Time", "Parent Node", "Interface Name"])
    for idx, item in enumerate(down_interfaces, start=1):
        ws_interfaces.append([idx, item['downtime'], item['parent'], item['name']])

    excel_filename = "down_report.xlsx"
    wb.save(excel_filename)
    print(f"[+] Excel report successfully saved to {excel_filename}")

if __name__ == "__main__":
    main()