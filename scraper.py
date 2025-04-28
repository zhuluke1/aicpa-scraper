import requests
from bs4 import BeautifulSoup
import time

# Scrape AICPA standards page
url = "https://www.aicpa.org/resources/standards"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Example: Extract resource titles (adjust based on actual HTML)
    for title in soup.find_all("h2"):
        print(title.text.strip())
    
    time.sleep(1)  # Rate limiting
except requests.RequestException as e:
    print(f"Error fetching {url}: {e}")