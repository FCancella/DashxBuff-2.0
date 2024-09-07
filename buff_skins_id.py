import html
import re
import requests
import json
import os

def clear_item_name(name):
    # Decode HTML entities, replace single quotes, and remove non-alphanumeric characters
    cleared_name = re.sub(r'[^a-zA-Z0-9]', '', html.unescape(name.replace("'", ""))).lower().replace("27","") # Work around for "Case Key" and "Capsule Key", since buff doesn't sell it
    return cleared_name

def check_item_dash_qnt(name):
    url = f"https://api.dashskins.gg/v1/item?pageSize=1000&partialMarketHashName={name}"
    count_per_item = 0
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (non-2xx status codes)

        # Parse the JSON response
        data = response.json()
        
        #item_qnt = data.get("totalItems")

        # Extract the page items
        page_items = data.get('page', [])

        # Count how many times the provided name appears as marketHashName in each item
        for item in page_items:
            if item.get("marketHashName") == name:
                count_per_item+=1
        #count_per_item = {item['id']: item['marketHashName'] == name for item in page_items}

        return count_per_item

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return count_per_item


'''
def access_api_with_cookies(cookie_data, goods_id):
    url = f"https://buff.163.com/api/market/goods/price_history/buff?game=csgo&goods_id={goods_id}&currency=BRL&days=30&buff_price_type=2&with_sell_num=false"

    with requests.Session() as session:
        session.headers.update({'Cookie': cookie_data})
        
        try:
            response = session.get(url)
            if response.status_code == 200:
                return analyze_price_history(response.json())
            else:
                print(f"Error: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Error: {e}")
            return False

def analyze_price_history(data):
    # Extract the price history from the response data
    price_history = data.get('data', {}).get('price_history', [])

    # Take the last 17 prices (15 + the 2 excluded)
    last_prices = price_history[-17:]

    # Exclude the last two prices from the mean calculation
    last_two_prices = last_prices[-1:]
    mean_last_two_prices = sum(price[1] for price in last_two_prices) / 1

    # Get the last 15 prices (17 - 2)
    mean_prices = last_prices[:-2]

    # Get the mean of the last 15 prices
    mean_last_15_prices = sum(price[1] for price in mean_prices) / len(mean_prices)

    # Check if the most recent price is 5% higher than the mean of the last 15 prices
    print("\n", mean_last_15_prices, mean_last_two_prices)
    return (mean_last_two_prices > mean_last_15_prices*1.05)
'''


def load_id_dict():
    # URL of the text file containing the ids
    url = "https://raw.githubusercontent.com/ModestSerhat/buff163-ids/main/buffids.txt"

    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (non-2xx status codes)

        # Parse the response content
        return parse_response(response.text)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

        # Specify the path to the backup file in the same directory as the script
        backup_file = os.path.join(os.path.dirname(__file__), "backup_ids_12_2023.txt")

        if os.path.isfile(backup_file):
            # Ask the user if they want to use the backup file
            use_backup = input("Backup file not found. Do you want to use the stored backup? (y/n): ").lower()

            if use_backup == 'y':
                # Read the content of the backup file with proper encoding (utf-8)
                with open(backup_file, 'r', encoding='utf-8') as file:
                    backup_content = file.read()

                # Parse the content of the backup file
                return parse_response(backup_content)
            else:
                print("Backup not loaded. Exiting...")
                exit(1)
        else:
            print(f"Backup file not found: {backup_file}. Exiting...")
            exit(1)

def parse_response(content):
    lines = content.strip().split('\n')
    id_dict = {}

    for line in lines:
        item_id, item_name = map(str.strip, line.split(';'))
        cleaned_key = clear_item_name(item_name)
        id_dict[cleaned_key] = int(item_id)

    return id_dict


id_dict = load_id_dict()

def all_items_data_dict():
    url = "http://csgobackpack.net/api/GetItemsList/v2/"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses
        data = response.json()
        items_list = data.get("items_list", {})

        # Organize the data into a dictionary with classid as keys and only name and price as values
        result_dict = {}
        '''
        result_dict = {
        id1: [30d, 7d, 24h],
        id2: [30d, 7d, 24h],
        id3: [30d, 7d, 24h],
        }
        '''

        for item_data in items_list.values():
            # Check if the item_data has the 'price' key
            if "price" in item_data and \
                "Case Key" not in item_data["name"] and \
                "Capsule Key" not in item_data["name"] and \
                "Capsule 1 Key" not in item_data["name"] and \
                "ESL Cologne 2014" not in item_data["name"] and \
                "eSports Key" not in item_data["name"]:
                
                item_cleared_name = clear_item_name(item_data["name"])
                item_id = id_dict.get(item_cleared_name)

                # Get the number of items sold in the last 30/7 days and past 24 hours (with defaults set to 0)
                sold_30_days = int(item_data["price"].get("30_days", {}).get("sold", 0)) if item_data["price"].get("30_days", {}).get("sold") else 0
                sold_7_days = int(item_data["price"].get("7_days", {}).get("sold", 0)) if item_data["price"].get("7_days", {}).get("sold") else 0
                sold_24_hours = int(item_data["price"].get("24_hours", {}).get("sold", 0)) if item_data["price"].get("24_hours", {}).get("sold") else 0

                result_dict[item_id] = [item_cleared_name, [sold_30_days, sold_7_days, sold_24_hours]]

        return result_dict

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from the URL: {e}")
        return None

