import requests

def get_tech_news():
    try:
        hn_ids = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:3]
        hn_stories = []
        for hid in hn_ids:
            story = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{hid}.json').json()
            hn_stories.append(story.get('title', 'Unknown Title'))
        return hn_stories
    except Exception:
        return ["Tech news unavailable."]
