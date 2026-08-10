import re
from bs4 import BeautifulSoup
import config

def parse_report_html(html_content, entity_type="Node"):
    """Parses report HTML and returns list of item dictionaries with detail links."""
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
        
        # 1. Skip table headers
        if "node" in col_texts or "interface" in col_texts or "status" in col_texts or "views:" in row_text:
            continue

        # 2. Check for explicit down icon
        is_hard_down = False
        img_tags = row.find_all("img")
        for img in img_tags:
            if img.has_attr("src") and "small-Down.gif" in img["src"]:
                is_hard_down = True
                break

        # 3. Detect parent node header row for interface reports
        if entity_type == "Interface" and not is_hard_down and len(cols) <= 2:
            link_tag = row.find("a")
            current_node = link_tag.get_text(strip=True) if link_tag else row.get_text(strip=True)
            continue  
        
        # 4. Extract Entity Name and Detail URL
        if is_hard_down:
            for col in cols:
                link_tag = col.find("a")
                if link_tag and link_tag.has_attr('href'):
                    item_name = link_tag.get_text(strip=True)
                    url_path = link_tag['href']
                    
                    if item_name:
                        full_url = url_path if url_path.startswith("http") else f"{config.BASE_URL}{url_path}"
                        down_items.append({
                            "type": entity_type,
                            "parent": current_node,
                            "name": item_name,
                            "url": full_url
                        })
                        break
                        
    return down_items