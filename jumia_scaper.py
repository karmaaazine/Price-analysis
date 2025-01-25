from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import os

# Constants
BASE_URL = "https://www.jumia.ma"
START_URL = "https://www.jumia.ma/refrigerateurs-frigo"
MAX_PAGES = 30
OUTPUT_DIR = "jumia"

# Selenium Setup
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")
service = Service("C:/chromedriver.exe")  # Adjust the path to your ChromeDriver
driver = webdriver.Chrome(service=service, options=options)

def get_data(url):
    """
    Fetches the page source using Selenium.
    """
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "prd"))
    )
    return driver.page_source


def parse(html):
    """
    Parses product information from the HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Debug: Print a preview of the page to confirm if products are present
    print(soup.prettify()[:1000])  # Show the first 1000 characters for debugging

    results = soup.find_all('div', {'class': 'info'})
    print(f"Found {len(results)} product entries.")

    if not results:
        print("No products found. Check the HTML structure or URL.")
        return []

    all_products = []
    collection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for item in results:
        try:
            # Extract Product Name
            product_name_tag = item.find('h3', class_='name')
            product_name = product_name_tag.text.strip() if product_name_tag else 'N/A'
            print(f"Product Name: {product_name}")  # Debugging product name

            # Extract Product Link
            parent_a_tag = item.find_parent('a')
            link = parent_a_tag['href'] if parent_a_tag else 'N/A'
            if link and not link.startswith('http'):
                link = BASE_URL + link
            print(f"Product Link: {link}")

            # Extract Promo Price
            price_promo_tag = item.find('div', class_='prc')
            price_promo = (
                float(price_promo_tag.text.replace('Dhs', '').replace(',', '').strip())
                if price_promo_tag
                else 'N/A'
            )
            print(f"Promo Price: {price_promo}")  # Debugging promo price

            # Extract Initial Price (Old Price)
            old_price_tag = item.find('div', class_='old')
            price_initial = (
                float(old_price_tag.text.replace('Dhs', '').replace(',', '').strip())
                if old_price_tag
                else 'N/A'
            )
            print(f"Initial Price: {price_initial}")  # Debugging initial price

            # Product Object
            product = {
                'productName': product_name,
                'marketplace': 'Jumia',
                'category': 'Mode, Vêtements et Accessoires',
                'link': link,
                'priceInitial': price_initial,
                'pricePromo': price_promo,
                'collectionTime': collection_time
            }
            all_products.append(product)

        except Exception as e:
            print(f"Error parsing product: {e}")
            print(f"Product HTML: {item.prettify()[:500]}")  # Debug the specific item
            continue

    return all_products


def get_next_page(soup):
    """
    Identifies the URL for the next page.
    """
    next_button = soup.find('a', {'aria-label': 'Page suivante'})
    if next_button and 'href' in next_button.attrs:
        return BASE_URL + next_button['href']
    return None

def log_run():
    """
    Logs the run timestamp into a text file.
    """
    log_file = os.path.join(OUTPUT_DIR, 'jumia_log.txt')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as file:
        file.write(f"Code run at: {current_time}\n")

# Main Execution
if __name__ == "__main__":
    log_run()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    current_url = START_URL
    all_products = []
    page_count = 0

    try:
        while current_url and page_count < MAX_PAGES:
            print(f"Fetching page {page_count + 1}: {current_url}")
            html = get_data(current_url)
            products = parse(html)
            all_products.extend(products)
            soup = BeautifulSoup(html, 'html.parser')
            current_url = get_next_page(soup)
            page_count += 1

        if all_products:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join(OUTPUT_DIR, f"jumia_products_{timestamp}.csv")
            df = pd.DataFrame(all_products)
            df.to_csv(filename, index=False)
            print(f"Products saved to {filename}")
        else:
            print("No products found.")
    finally:
        driver.quit()






