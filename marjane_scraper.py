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
BASE_URL = "https://www.marjanemall.ma"
START_URL = "https://www.marjanemall.ma/vetements-chaussures-bijoux-accessoires"
MAX_PAGES = 30
OUTPUT_DIR = "marjane_mall"

# Selenium Setup
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
service = Service("C:/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

def get_data(url):
    """
    Fetches the page source using Selenium.
    """
    driver.get(url)
    # Wait for the product grid to be loaded (example: adjust this if the class name is different)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "product-item-link"))
    )
    return driver.page_source

def parse(html):
    """
    Parses product information from the HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Debug: Print a preview of the page to confirm if products are present
    print(soup.prettify()[:1000])  # Show the first 1000 characters for debugging
    
    results = soup.find_all('div', {'class': 'product-item-details'})
    print(f"Found {len(results)} product entries.")
    
    if not results:
        print("No products found. Check the HTML structure or URL.")
        return []

    all_products = []
    collection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for item in results:
        try:
            # Product Name
            product_name_tag = item.find('a', {'class': 'product-item-link'})
            product_name = product_name_tag.text.strip() if product_name_tag else 'N/A'
            print(f"Product Name: {product_name}")  # Debugging product name

            # Product Link
            link_tag = product_name_tag
            link = link_tag['href'] if link_tag else 'N/A'
            if link and not link.startswith('http'):
                link = BASE_URL + link

            # Initial Price
            oldPrice = item.find('span', {'class': 'old-price sly-old-price'})
            if oldPrice:
                price_initial_tag = oldPrice.find('span', {'class': 'price-wrapper'})
                if price_initial_tag and 'data-price-amount' in price_initial_tag.attrs:
                    price_initial = float(price_initial_tag['data-price-amount'])
                else:
                    price_initial = 'N/A'
            else:
                price_initial = 'N/A'

            print(f"Initial Price: {price_initial}")  # Debugging price
            
            # Promo Price (Optional)
            price_promo_tag = item.find('span', {'class': 'price-wrapper'})
            if price_promo_tag and 'data-price-amount' in price_promo_tag.attrs:
                price_promo = float(price_promo_tag['data-price-amount'])
            else:
                price_promo = 'N/A'

            # Product Object
            product = {
                'productName': product_name,
                'marketplace': 'Marjane Mall',
                'category': 'Clothing, Shoes & Jewelry',
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
    try:
        next_button = soup.find('li', {'class': 'item pages-item-next'})
        if next_button:
            link_tag = next_button.find('a')
            if link_tag and 'href' in link_tag.attrs:
                next_page = link_tag['href']
                if not next_page.startswith('http'):
                    next_page = BASE_URL + next_page
                return next_page
    except Exception as e:
        print(f"Error finding next page: {e}")
    return None

def log_run():
    """
    Logs the run timestamp into a text file each time the code is executed.
    """
    log_file = 'marjane_mall/marjane_log.txt'
    # Get the current time and format it
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Open the log file in append mode and write the log entry
    with open(log_file, 'a') as file:
        file.write(f"Code run at: {current_time}\n")

# Main Execution
if __name__ == "__main__":
    log_run()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    page_count = 0
    all_products = []

    try:
        current_url = START_URL

        while current_url and page_count < MAX_PAGES:
            print(f"Fetching page {page_count + 1}: {current_url}")
            html = get_data(current_url)
            products = parse(html)
            all_products.extend(products)

            page_count += 1
            soup = BeautifulSoup(html, 'html.parser')
            current_url = get_next_page(soup)
            if not current_url:
                print("No more pages available.")
                break

        if all_products:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join(OUTPUT_DIR, f"marjaneMall_products_{timestamp}.csv")
            df = pd.DataFrame(all_products)
            df.to_csv(filename, index=False)
            print(f"Products saved to {filename}")
        else:
            print("No products found.")
    finally:
        driver.quit()
