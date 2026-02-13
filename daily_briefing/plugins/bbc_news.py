import requests
import xml.etree.ElementTree as ET

def get_bbc_news():
    try:
        res = requests.get("http://feeds.bbci.co.uk/news/rss.xml")
        res.raise_for_status()
        root = ET.fromstring(res.content)
        
        headlines = []
        # namespace handling can be tricky, but standard RSS usually has item under channel
        for item in root.findall(".//item")[:3]:
            title = item.find("title").text
            headlines.append(title)
            
        return headlines
    except Exception as e:
        return [f"BBC News unavailable: {e}"]
