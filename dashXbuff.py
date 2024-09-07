import time
import pandas as pd

# Modules
from cny2brl import cny_brl_rate
from buff_skins_id import load_id_dict, clear_item_name
from auxiliary import loading_bar

import requests
import sys
import concurrent.futures

# Change the encoding to UTF-8 because of the special characters in the skin names
sys.stdout.reconfigure(encoding='utf-8')

# Call the function to get the Yuan to Brazilian Real exchange rate
yuan_brl_rate = cny_brl_rate()
print("* CNY/BRL rate successfully updated!")


price_min = 10
price_max = 2000

# Define the Buff ID dictionary (skin_name: buff_id)
id_dict = load_id_dict()
'''
id_dict = {
'skin_1': id1,
'skin_2': id2,
'skin_3': id3,
}
'''
print("* Buff ID dictionary successfully loaded")


# Receive a skin's name and return its price and the number of offers on Buff
def get_skin_data(product_name):
    # Get the item's Buff ID by searching the dictionary.
    item_id = id_dict.get(product_name)

    buff_api_url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&page_num=1&goods_id={item_id}"

    while True:
        try:
            # Send a GET request to the API
            response = requests.get(buff_api_url)
            response.raise_for_status()  # Raise an exception for bad responses (non-2xx status codes)

            # Parse the JSON response
            data = response.json()

            # Extract the "items" list
            items_list = data.get("data", {}).get("items", [])

            if items_list:
                # If the list is not empty, extract the "price" value from the first item
                buff_price = items_list[0].get("price")
                buff_price = float(buff_price) * yuan_brl_rate
                buff_offers = data.get("data", {}).get("total_count", 0)
                break  # Exit the loop if successful
            else:
                #print(f"'{product_name}' price information not found in the response")
                buff_price = 0
                buff_offers = 0
                break

        except requests.RequestException as e:
            None
            #warning(f"An error occurred: {str(e)}\n{product_name} fetch failed...")

        # Sleep before retrying
        time.sleep(0.2)

    buff_price = round(buff_price, 2)

    return [buff_price, buff_offers]




# Dict to store checked skins and their prices (prevent scraping the same item multiple times)
products = {}
'''
products = {
'skin_1': price_1,
'skin_2': price_2,
'skin_3': price_3,
}
'''

item_counter = 0

print("* Initializing DashSkins api analysis")
dash_api_url = f"https://api.dashskins.gg/v1/item?pageSize=100000&maxPriceBRL={price_max}&minPriceBRL={price_min}&sort=discount-desc"

# Send a GET request to the API
response = requests.get(dash_api_url)

# Parse the JSON response
data = response.json()

# Extract the "items" list
dash_items_list = data.get("page", [])

if dash_items_list:
    for item in dash_items_list:
        name = item.get("marketHashName")
        #dash_id = item.get("id")
        cleared_name = clear_item_name(name)
        price = item.get("priceBRL")

        # Skip if item is a case key (not available on buff)
        if "case key" in name.lower():
            continue
        
        # Get the item's Buff ID
        item_id = id_dict.get(cleared_name)

        #Check if the item qualifies for the items list
        if name in products and price >= products[name]:
            # Skip this item as it's more expensive than the one already seen
            continue
        
        # Add/Update the item on the dictionary of viewed items
        products[name] = price

print(f"* DashSkins parse concluded. {len(dash_items_list)} item's analyzed")

print()


item_counter = 0

linha = []

total_items = len(products.keys())

print("\nScraping and analysing items")

# Define a function to process a single product
def process_product(product_name):
    global item_counter

    item_counter+=1
    loading_bar(item_counter, total_items)

    formated_product_name = clear_item_name(product_name)
        
    if ("Sticker" in product_name):
        # End function withou even searching this item on buff api
        return

    dash_price = products[product_name]

    # Get the price and offers for the product on the 'Buff163' platform
    [buff_price, buff_offers] = get_skin_data(formated_product_name)

    # Percentage difference between Buff163 and DashSkins (Dash + % = Buff)
    diff = int((buff_price / dash_price - 1) * 100)

    # Adjust dash's price if the spread is lower than -15%, indicating that it's an item for sale from 'Buff163' to 'Dashskins'.
    # Note1: -10% -> default selling fee on Dashskins.
    # Note2: -5% -> margin to sell even cheaper.
    # Note3: < -15% is being used because with [-15%, 0%], the calculation would turn the number into a positive percentage.
    if diff < -15:
        diff = int((buff_price / (dash_price*0.85) - 1) * 100)
    elif  -15 <= diff and diff <= 0:
        diff = 0 # this item ain't relevant
    
    #print(f"{'R$'+str(dash_price):9} | BUFF {('R$' + str(buff_price)):^12} | {diff:3}% | {buff_offers:2} | \t{product_name}")

    if (buff_offers >= 91 and diff > 2) or \
        (buff_offers >= 91 and diff < -15 and \
        dash_price/buff_price <= 3 and \
        # Price difference can't be >300% (unreal)
        "Sticker" not in product_name):

        # Adiciona uma nova linha ao dataframe com as informações do produto
        linha.append([product_name, dash_price, buff_price, diff, buff_offers])

# Create a ThreadPoolExecutor with 2 concurrent threads ( More than 2 usually equals API errors)
with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
    # Use the executor to process products concurrently
    results = list(executor.map(process_product, products.keys()))


print("\n\nITEMS\n\n")

# Sort the list based on the "diff" field (4th element in each sublist)
sorted_linha = sorted(linha, key=lambda x: x[3], reverse=True)

# Create a DataFrame from the sorted list
df = pd.DataFrame(sorted_linha, columns=["Product Name", "Dash Price", "Buff Price", "Diff", "Buff Offers"])

# Save the DataFrame as a CSV file
df.to_csv("skins.csv", index=False)

# Print the DataFrame (optional)
print(df)
