import time
import csv
import string
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Base URL for AICPA-CIMA directory
BASE_URL = "https://www.aicpa-cima.com/directories/results/%3FlastName={last_name}&pageNumber={page}&pageSize=12&searchType=3"


def generate_last_names():
    """Generate all two-letter combinations from aa to zz."""
    letters = string.ascii_lowercase
    return [f"{a}{b}" for a in letters for b in letters]


def get_total_pages(driver):
    """Extract total number of pages from the results header using Selenium."""
    try:
        # Wait for the result count span to appear (using the class from your HTML)
        results_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.sc-gcFgsk.bEPHOJ"))
        )
        text = results_span.text
        print(f"Found results text: {text}")
        # Extract total results (e.g., "Showing 13 - 24 of 52 search results")
        if "of" in text:
            total_results = int(text.split("of")[-1].split("search")[0].strip())
            return math.ceil(total_results / 12)
    except TimeoutException:
        print("Timeout waiting for results count")
    except Exception as e:
        print(f"Error getting total pages: {str(e)}")
    return 1


def extract_entries(driver):
    """Extract directory entries from the table using Selenium."""
    entries = []
    try:
        # Wait for table to be present
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.ui.table"))
        )
        print("Found table element")
        
        # Wait for tbody
        tbody = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        print("Found tbody element")
        
        # Get all rows
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        print(f"Found {len(rows)} rows")
        
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                # Always get 4 columns, fill with empty string if missing
                values = [cols[i].text.strip() if i < len(cols) else '' for i in range(4)]
                # Only add if at least one column is non-empty
                if any(values):
                    print(f"Found entry: {values}")
                    entries.append(values)
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
                
    except TimeoutException:
        print("Timeout waiting for table elements")
    except Exception as e:
        print(f"Error extracting entries: {str(e)}")
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
    # Set up Selenium WebDriver (Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    last_names = generate_last_names()

    for last_name in last_names:
        print(f"\nScraping last name: {last_name}")
        url = BASE_URL.format(last_name=last_name, page=1)
        print(f"Accessing URL: {url}")
        
        try:
            driver.get(url)
            time.sleep(5)  # Increased wait time
            
            # Print page title and current URL for debugging
            print(f"Page title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            
            # Try to find the table first
            try:
                table = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.ui.table"))
                )
                print("Found table element")
            except TimeoutException:
                print(f"No table found for last name: {last_name}")
                continue

            # Get total pages for this last name
            total_pages = get_total_pages(driver)
            print(f"Total pages for {last_name}: {total_pages}")

            # Scrape first page entries
            entries = extract_entries(driver)
            if entries:
                save_to_csv(entries)
                print(f"Saved {len(entries)} entries")

            # Scrape remaining pages
            for page in range(2, total_pages + 1):
                print(f"\nScraping page {page} for {last_name}")
                url = BASE_URL.format(last_name=last_name, page=page)
                print(f"Accessing URL: {url}")
                driver.get(url)
                time.sleep(5)
                entries = extract_entries(driver)
                if entries:
                    save_to_csv(entries)
                    print(f"Saved {len(entries)} entries")
                time.sleep(2)  # Increased rate limiting

            time.sleep(3)  # Additional delay between last names
            
        except Exception as e:
            print(f"Error processing {last_name}: {str(e)}")
            continue

    driver.quit()

if __name__ == "__main__":
    main() 