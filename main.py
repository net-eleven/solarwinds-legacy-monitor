# main.py
from login import OrionClient
from fetch import Fetch
import parse

def main():
    print("=== NOC AUTOMATION START ===")

    client = OrionClient()
    if not client.authenticate():
        print("[-] Exiting due to authentication failure.")
        return

    # 1. Fetch DOWN NODES
    node_html = Fetch.fetch_nodes(client)
    down_nodes = parse.parse_report_html(node_html, "Node") if node_html else []
    for node in down_nodes:
        print(node)
    print(f"The lenght of node is {len(down_nodes)}")


    # 2. Fetch DOWN INTERFACES 
    interface_html = Fetch.fetch_interfaces(client)
    down_interfaces = parse.parse_report_html(interface_html, "Interface") if interface_html else []


    with open("down.txt", "w", encoding="utf-8") as f:
        f.write("==== DOWN NODES ====\n")
        f.write("\n".join(down_nodes) + "\n")

        f.write("\n\n\n")
        

        f.write("==== DOWN INTERFACES ====\n")
        f.write("\n".join(down_interfaces) + "\n")
    


    
    
    
    

if __name__ == "__main__":
    main()
