import time
import openpyxl
from login import OrionClient
from fetch import Fetch
import parse

def process_items_sequential(fetcher, client, items_list, delay=0.1):
    """Fetches downtime timestamps strictly one by one to avoid IIS session locking."""
    processed = []
    total = len(items_list)
    
    for idx, item in enumerate(items_list, start=1):
        downtime = fetcher.fetch_downtime(client, item)
        item['downtime'] = downtime
        
        # Build full name string
        if item['type'] == 'Interface':
            item['full_name'] = f"{item['parent']} -> {item['name']}"
        else:
            item['full_name'] = item['name']
            
        item['display_str'] = f"[{downtime}] {item['full_name']}"
        processed.append(item)
        
        # Live progress log in terminal
        print(f"  [{idx}/{total}] {downtime} - {item['full_name']}")
        
        # Brief pause to keep legacy server happy
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
    down_nodes = process_items_sequential(fetcher, client, raw_nodes, delay=0.1)

    # 2. Fetch & Parse DOWN INTERFACES 
    interface_html = fetcher.fetch_interfaces(client)
    raw_interfaces = parse.parse_report_html(interface_html, "Interface") if interface_html else []
    print(f"[*] Processing {len(raw_interfaces)} Down Interfaces sequentially...")
    down_interfaces = process_items_sequential(fetcher, client, raw_interfaces, delay=0.1)

    # 3. Write text output (down.txt)
    with open("down.txt", "w", encoding="utf-8") as f:
        f.write("==== DOWN NODES ====\n")
        f.write("\n".join([n['display_str'] for n in down_nodes]) + "\n\n\n")

        f.write("==== DOWN INTERFACES ====\n")
        f.write("\n".join([i['display_str'] for i in down_interfaces]) + "\n")
    print("\n[+] Text report successfully saved to down.txt")

    # 4. Write Excel output (down_report.xlsx)
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