import re
from bs4 import BeautifulSoup

def parse_report_html(html_content, entity_type="Node"):
    """Parses down nodes or interfaces, drops headers, and extracts actual down times."""
    soup = BeautifulSoup(html_content, "html.parser")
    down_items = []
    
    current_node = "Unknown-Node"
    
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all(["td", "th"])
        if not cols:
            continue
            
        row_text = row.get_text(strip=True).lower()
        col_texts = [c.get_text(strip=True).lower() for c in cols]
        
        # 1. Brutal Header Execution
        if "node" in col_texts or "interface" in col_texts or "status" in col_texts or "views:" in row_text:
            continue

        # 2. Check for the explicit 'small-Down.gif' status icon first
        is_hard_down = False
        img_tags = row.find_all("img")
        for img in img_tags:
            if img.has_attr("src") and "small-Down.gif" in img["src"]:
                is_hard_down = True
                break

        # 3. Detect parent Node header row (for Interface reports)
        if entity_type == "Interface" and not is_hard_down and len(cols) <= 2:
            link_tag = row.find("a")
            current_node = link_tag.get_text(strip=True) if link_tag else row.get_text(strip=True)
            continue  
        
        # 4. Extract the actual down entity and its actual down time
        if is_hard_down:
        

            for col in cols:
                link_tag = col.find("a")
                if link_tag:
                    item_name = link_tag.get_text(strip=True)
                    
                    if item_name:
                        if entity_type == "Interface":
                            formatted_entry = f"{current_node} -> {item_name}"
                        else:
                            formatted_entry = f"{item_name}"
                            
                        if formatted_entry not in down_items:
                            down_items.append(formatted_entry)
                        break
                        
    return down_items