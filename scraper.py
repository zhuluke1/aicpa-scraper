import requests
from bs4 import BeautifulSoup
import time
import csv
import string
import math
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Base URL for AICPA-CIMA directory
BASE_URL = "https://www.aicpa-cima.com/directories/results/%3FlastName={last_name}&pageNumber={page}&pageSize=12&searchType=3"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}

def generate_last_names():
    """Generate all two-letter combinations from aa to zz."""
    letters = string.ascii_lowercase
    return [f"{a}{b}" for a in letters for b in letters]

def get_total_pages(soup):
    """Extract total number of pages from the results header."""
    if not soup:
        return 1
    
    # Try the original selector
    results_div = soup.find("div", class_="sc-dxLkBQ jHKcIp")
    if not results_div:
        # Debug: Print HTML to find the correct selector
        print("Could not find results div with class 'sc-dxLkBQ jHKcIp'. Searching for alternative...")
        print(soup.prettify()[:1000])  # First 1000 chars of HTML for debugging
        
        # Fallback: Look for any div containing "search results"
        results_div = soup.find("div", string=lambda text: "search results" in text.lower() if text else False)
        if not results_div:
            print("No 'search results' div found. Assuming 1 page.")
            return 1
    
    # Find the span with the results count
    results_span = results_div.find("span") if results_div else None
    if not results_span:
        print("Could not find results span. HTML snippet:")
        print(results_div.prettify() if results_div else "No results div")
        return 1
    
    # Extract total results (e.g., "13 - 24 of 52 search results")
    try:
        total_results = int(results_span.text.split("of")[-1].split("search")[0].strip())
        # Calculate total pages (12 results per page)
        return math.ceil(total_results / 12)
    except (ValueError, IndexError) as e:
        print(f"Error parsing total results: {e}")
        return 1

def scrape_page(last_name, page):
    """Scrape a single page for a given last name and page number."""
    url = BASE_URL.format(last_name=last_name, page=page)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        print(response.text[:2000])
        return soup
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_entries(soup):
    """Extract directory entries from the page."""
    entries = []
    if not soup:
        return entries
    
    tbody = soup.find("tbody")
    if not tbody:
        print("No tbody found. HTML snippet:")
        print(soup.prettify()[:1000])  # First 1000 chars for debugging
        return entries
    
    for row in tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 4:
            name = cols[0].text.strip()
            status = cols[1].text.strip()
            location = cols[2].text.strip()
            date = cols[3].text.strip()
            entries.append([name, status, location, date])
    return entries

def save_to_csv(entries, filename="aicpa_directory.csv"):
    """Save scraped entries to a CSV file."""
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if f.tell() == 0:
            writer.writerow(["Name", "Status", "Location", "Date"])
        writer.writerows(entries)

def main():
    # Generate all last name combinations (aa to zz)
    last_names = generate_last_names()
    
    for last_name in last_names:
        print(f"Scraping last name: {last_name}")
        # Start with page 1 to get total pages
        soup = scrape_page(last_name, 1)
        if not soup:
            continue
        
        # Check if there are any results
        if not soup.find("tbody"):
            print(f"No results found for last name: {last_name}")
            continue
        
        # Get total pages for this last name
        total_pages = get_total_pages(soup)
        print(f"Total pages for {last_name}: {total_pages}")
        
        # Scrape first page entries
        entries = extract_entries(soup)
        if entries:
            save_to_csv(entries)
        
        # Scrape remaining pages
        for page in range(2, total_pages + 1):
            print(f"Scraping page {page} for {last_name}")
            soup = scrape_page(last_name, page)
            if soup:
                entries = extract_entries(soup)
                if entries:
                    save_to_csv(entries)
            time.sleep(1)  # Rate limiting

        time.sleep(2)  # Additional delay between last names

if __name__ == "__main__":
    main()