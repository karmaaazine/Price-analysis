import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request

# Fonction pour scraper Jumia
def scrape_jumia():
    url = "https://www.jumia.com.ng/catalog/?q=laptop"
    products = []
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de Jumia : {e}")
        return products

    soup = BeautifulSoup(response.content, "html.parser")
    for item in soup.find_all("article", class_="prd _fb col c-prd"):
        try:
            name = item.find("h3", class_="name").text.strip()
            price = item.find("div", class_="prc").text.strip().replace("₦", "").replace(",", "")
            price = float(price)
            products.append({
                "Nom": name,
                "Prix": price,
                "Site": "Jumia",
                "Categorie": "Électronique",
                "Date": "2025-01-01",
                "Promotion": "Aucune"
            })
        except AttributeError:
            continue
    return products

# Fonction pour scraper eBay
def scrape_ebay():
    url = "https://www.ebay.com/sch/i.html?_nkw=laptop"
    products = []
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement d'eBay : {e}")
        return products

    soup = BeautifulSoup(response.content, "html.parser")
    for item in soup.find_all("li", class_="s-item"):
        try:
            name = item.find("h3", class_="s-item__title").text.strip()
            price = item.find("span", class_="s-item__price").text.strip().replace("$", "").replace(",", "")
            price = float(price)
            products.append({
                "Nom": name,
                "Prix": price,
                "Site": "eBay",
                "Categorie": "Électronique",
                "Date": "2025-01-01",
                "Promotion": "Aucune"
            })
        except AttributeError:
            continue
    return products

# Fonction pour scraper Cdiscount
def scrape_cdiscount():
    url = "https://www.cdiscount.com/search/10/laptop.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    products = []
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de Cdiscount : {e}")
        return products

    soup = BeautifulSoup(response.content, "html.parser")
    for item in soup.find_all("div", class_="prdtBloc"):
        try:
            name = item.find("div", class_="prdtBILTit").text.strip()
            price = item.find("span", class_="price").text.strip().replace("€", "").replace(",", ".")
            price = float(price)
            products.append({
                "Nom": name,
                "Prix": price,
                "Site": "Cdiscount",
                "Categorie": "Électronique",
                "Date": "2025-01-01",
                "Promotion": "Aucune"
            })
        except AttributeError:
            continue
    return products

# Collecte des données des trois sites
def collect_all_data():
    jumia_data = scrape_jumia()
    ebay_data = scrape_ebay()
    cdiscount_data = scrape_cdiscount()

    # Combiner les données dans un DataFrame unique
    all_data = pd.DataFrame(jumia_data + ebay_data + cdiscount_data)
    return all_data

# Récupérer les données
raw_data = collect_all_data()

# Nettoyage et préparation des données
def clean_data(raw_data):
    if raw_data.empty:
        print("Aucune donnée n'a été collectée.")
        return pd.DataFrame()

    raw_data = raw_data.copy()  # Crée une copie explicite
    raw_data["Prix"] = pd.to_numeric(raw_data["Prix"], errors="coerce")
    raw_data = raw_data.dropna(subset=["Prix"]).drop_duplicates(subset=["Nom", "Site", "Date"])
    return raw_data

clean_data = clean_data(raw_data)

# Analyse et visualisation
def analyze_and_visualize(data):
    if data.empty:
        print("Pas de données à analyser.")
        return

    # Comparaison des prix moyens par site
    price_comparison = data.groupby(["Nom", "Site"])[["Prix"]].mean().unstack()
    price_comparison.plot(kind="bar", figsize=(12, 6), title="Comparaison des prix par site", colormap="viridis")
    plt.ylabel("Prix moyen (USD)")
    plt.xticks(rotation=45, ha="right")  # Pivote les noms des produits pour les rendre lisibles
    plt.tight_layout()  # Ajuste automatiquement les marges
    plt.show()

analyze_and_visualize(clean_data)

# API Flask
app = Flask(__name__)

@app.route("/lowest_price", methods=["GET"])
def get_lowest_price():
    product_name = request.args.get("product")
    if not product_name:
        return jsonify({"error": "Veuillez fournir un nom de produit."}), 400

    product_data = clean_data[clean_data["Nom"].str.contains(product_name, case=False, na=False)]
    if product_data.empty:
        return jsonify({"error": "Produit non trouvé."}), 404

    lowest_price_row = product_data.loc[product_data["Prix"].idxmin()]
    return jsonify({
        "Produit": lowest_price_row["Nom"],
        "Prix le plus bas": lowest_price_row["Prix"],
        "Site": lowest_price_row["Site"]
    })

@app.route("/promotions", methods=["GET"])
def list_promotions():
    return jsonify(clean_data["Promotion"].value_counts().to_dict())

if __name__ == "__main__":
    app.run(debug=True)
