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
import re

# Constants
BASE_URL = "https://www.jumia.ma"
START_URL = "https://www.jumia.ma/pc-portables/"
MAX_PAGES = 30
OUTPUT_DIR = "Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Laptops.csv")

# Selenium Setup
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")
service = Service("C:/chromedriver.exe")  # Adjust the path to your ChromeDriver
driver = webdriver.Chrome(service=service, options=options)

def parse_product_name(product_name):
    """
    Extract structured information from the product name.
    """
    data = {
        "Brand": None,
        "Model": None,
        "Generation": None,
        "Processor": None,
        "RAM": None,
        "Storage": None,
    }

    # Extract brand
    brand_match = re.search(r'\b(HP|Dell|Lenovo|Asus|Acer|Apple|MSI|Samsung|Toshiba)\b', product_name, re.IGNORECASE)
    data["Brand"] = brand_match.group(1) if brand_match else "Unknown"

    # Extract model
    model_match = re.search(r'(EliteBook|ThinkPad|Inspiron|Pavilion|IdeaPad|MacBook|Predator|ZenBook|Aspire|OMEN|ROG|Satellite)?\s?\d+\s?[A-Za-z]*', product_name, re.IGNORECASE)
    data["Model"] = model_match.group(0).strip() if model_match else "Unknown"

    # Extract generation
    generation_match = re.search(r'(\d+)(?:[èé]me|th)?\s?(?:GEN|GÉNÉRATION|GÉN)', product_name, re.IGNORECASE)
    data["Generation"] = f"{generation_match.group(1)}th Gen" if generation_match else "Unknown"

    # Extract processor
    processor_match = re.search(r'(Core\s?i[3579]|Ryzen\s?\d+)', product_name, re.IGNORECASE)
    data["Processor"] = processor_match.group(1) if processor_match else "Unknown"

    # Extract RAM
    ram_match = re.search(r'(\d+)\s?Go', product_name, re.IGNORECASE)
    data["RAM"] = f"{ram_match.group(1)}GB" if ram_match else "Unknown"

    # Extract storage
    storage_match = re.search(r'(\d+\s?Go\s?(SSD|HDD))', product_name, re.IGNORECASE)
    data["Storage"] = storage_match.group(1).replace('Go', 'GB').strip() if storage_match else "Unknown"

    return data

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
    results = soup.find_all('div', {'class': 'info'})

    all_products = []
    collection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for item in results:
        try:
            # Extract Product Name
            product_name_tag = item.find('h3', class_='name')
            product_name = product_name_tag.text.strip() if product_name_tag else 'N/A'

            # Extract Product Link
            parent_a_tag = item.find_parent('a')
            link = parent_a_tag['href'] if parent_a_tag else 'N/A'
            if link and not link.startswith('http'):
                link = BASE_URL + link

            # Extract Promo Price
            price_promo_tag = item.find('div', class_='prc')
            price_promo = (
                float(price_promo_tag.text.replace('Dhs', '').replace(',', '').strip())
                if price_promo_tag
                else 'N/A'
            )

            # Extract Initial Price (Old Price)
            old_price_tag = item.find('div', class_='old')
            price_initial = (
                float(old_price_tag.text.replace('Dhs', '').replace(',', '').strip())
                if old_price_tag
                else 'N/A'
            )
            promotions = []
            promo_tags = item.find_all("div", class_="bdg _dsct _sm")  # Chercher toutes les balises avec classe "tag"
            for promo_tag in promo_tags:
                if promo_tag.text.strip():
                    promotions.append(promo_tag.text.strip())

            promotion = ", ".join(promotions) if promotions else 'Aucune'
            

            # Parse structured information from the product name
            structured_data = parse_product_name(product_name)

            # Product Object
            product = {
                'productName': product_name,
                **structured_data,
                'marketplace': 'Jumia',
                'category': 'PC Portables',
                'link': link,
                'priceInitial': price_initial,
                'pricePromo': price_promo,
                'promotiontype' : promotion,
                'collectionTime': collection_time,
                
            }
            all_products.append(product)

        except Exception as e:
            print(f"Error parsing product: {e}")
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

def save_to_csv(products):
    """
    Save product data to a single CSV file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(OUTPUT_FILE):
        pd.DataFrame(products).to_csv(OUTPUT_FILE, index=False)
    else:
        pd.DataFrame(products).to_csv(OUTPUT_FILE, mode='a', header=False, index=False)

# Main Execution
if __name__ == "__main__":
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
            save_to_csv(all_products)
            print(f"Products saved to {OUTPUT_FILE}")
        else:
            print("No products found.")
    finally:
        driver.quit()
