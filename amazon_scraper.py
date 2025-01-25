import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import random

# Constants
base_url = "https://www.amazon.com"
MAX_PAGES = 30
url = "https://www.amazon.com/s?i=fashion-womens-intl-ship&bbn=16225018011&rh=n%3A7141123011&dc&language=en_US"
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.amazon.com',
    'Connection': 'keep-alive',
}

# Ensure output directory exists
os.makedirs("amazon", exist_ok=True)

# Currency conversion
def get_exchange_rate():
    api_url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = httpx.get(api_url)
        data = response.json()
        return data['rates']['MAD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return 10.0  # Default fallback rate

usd_to_mad_rate = get_exchange_rate()

async def get_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADER)
        if response.status_code != 200:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return None
        return BeautifulSoup(response.text, 'html.parser')

async def parse(soup):
    results = soup.find_all('div', {'class': 'a-section a-spacing-small puis-padding-left-small puis-padding-right-small'})
    all_products = []  # To store all product data
    collection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for item in results:
        try:
            product_name = item.find('h2', {'class': 'a-size-base-plus a-spacing-none a-color-base a-text-normal'}).find('span')
            if product_name:
                product_name = product_name.text.strip()
            else:
                print("Product name not found.")
                continue  # Skip if the product name is not found

            link_tag = item.find('a', {'class': 'a-link-normal s-line-clamp-4 s-link-style a-text-normal'})
            link = link_tag['href'] if link_tag else 'N/A'
            link = base_url + link if link != 'N/A' else 'N/A'

            price_initial = item.find('span', {'class': 'a-price a-text-price'}).find('span', {'class': 'a-offscreen'})
            if price_initial:
                price_initial = float(price_initial.text.replace('$', '').strip())
                price_initial_mad = round(price_initial * usd_to_mad_rate, 2)
            else:
                price_initial = 'N/A'
                price_initial_mad = 'N/A'

            price_promo = item.find('span', {'class': 'a-price-whole'})
            if price_promo:
                price_promo = float(price_promo.text.replace('$', '').strip())
                price_promo_mad = round(price_promo * usd_to_mad_rate, 2)
            else:
                price_promo = 'N/A'
                price_promo_mad = 'N/A'

            product = {
                'productName': product_name,
                'marketplace': 'Amazon',
                'category': 'Mode, Vêtements et Accessoires',
                'link': link,
                'priceInitialUSD': price_initial,
                'priceInitialMAD': price_initial_mad,
                'pricePromoUSD': price_promo,
                'pricePromoMAD': price_promo_mad,
                'collectionTime': collection_time
            }
            all_products.append(product)
        except AttributeError as e:
            print(f"Error parsing product: {e}")
            continue  # Skip the product if any key element is missing

    return all_products

def get_next_page(soup):
    next_page_tag = soup.find('a', {'class': 's-pagination-item s-pagination-next'})
    return base_url + next_page_tag['href'] if next_page_tag else None

def log_run():
    """
    Logs the run timestamp into a text file each time the code is executed.
    """
    log_file = 'amazon/amazon_log.txt'
    # Get the current time and format it
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Open the log file in append mode and write the log entry
    with open(log_file, 'a') as file:
        file.write(f"Code run at: {current_time}\n")

async def main():
    log_run()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"amazon/amazon_products_{timestamp}.csv"
    all_products = []
    current_url = url
    page_count = 0

    while current_url and page_count < MAX_PAGES:
        print(f"Fetching page {page_count + 1}: {current_url}")
        soup = await get_data(current_url)
        if soup:
            products = await parse(soup)
            if products:
                all_products.extend(products)
                current_url = get_next_page(soup)
                await asyncio.sleep(random.uniform(1, 3))  # Delay
                page_count += 1
            else:
                break
        else:
            break

    if all_products:
        df = pd.DataFrame(all_products)
        df.to_csv(filename, index=False)
        print(f"Products saved to {filename}")

asyncio.run(main())
