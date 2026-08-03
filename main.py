from login import OrionClient
from fetch import Fetch
import parse
import openpyxl

def main():
    print("=== NOC AUTOMATION START ===")

    client = OrionClient()
    if not client.authenticate():
        print("[-] Exiting due to authentication failure.")
        return

    # 1. Fetch DOWN NODES
    node_html = Fetch.fetch_nodes(client)
    down_nodes = parse.parse_report_html(node_html, "Node") if node_html else []
    print(f"The length of node is {len(down_nodes)}")

    # 2. Fetch DOWN INTERFACES 
    interface_html = Fetch.fetch_interfaces(client)
    down_interfaces = parse.parse_report_html(interface_html, "Interface") if interface_html else []
    print(f"The length of interfaces is {len(down_interfaces)}")

    # 3. Write text output (down.txt)
    with open("down.txt", "w", encoding="utf-8") as f:
        f.write("==== DOWN NODES ====\n")
        f.write("\n".join(down_nodes) + "\n\n\n")
        f.write("==== DOWN INTERFACES ====\n")
        f.write("\n".join(down_interfaces) + "\n")

    # 4. Write Excel output (down_report.xlsx)
    wb = openpyxl.Workbook()
    
    # Sheet 1: Down Nodes
    ws_nodes = wb.active
    ws_nodes.title = "Down Nodes"
    ws_nodes.append(["Index", "Node Name"])
    for idx, node in enumerate(down_nodes, start=1):
        ws_nodes.append([idx, node])

    # Sheet 2: Down Interfaces
    ws_interfaces = wb.create_sheet(title="Down Interfaces")
    ws_interfaces.append(["Index", "Parent Node", "Interface Name"])
    
    for idx, entry in enumerate(down_interfaces, start=1):
        if "->" in entry:
            parts = entry.split("->", 1)
            parent = parts[0].strip()
            interface = parts[1].strip()
        else:
            parent = "Unknown"
            interface = entry
        ws_interfaces.append([idx, parent, interface])

    excel_filename = "down_report.xlsx"
    wb.save(excel_filename)
    print(f"[+] Excel report successfully generated: {excel_filename}")

if __name__ == "__main__":
    main()