import html
import re
import requests

def clear_item_name(name):
    # Decode HTML entities, replace single quotes, and remove non-alphanumeric characters
    cleared_name = re.sub(r'[^a-zA-Z0-9]', '', html.unescape(name.replace("'", ""))).lower().replace("27","") # Work around for "Case Key" and "Capsule Key", since buff doesn't sell it
    return cleared_name

'''
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

def load_id_dict():
    # URL of the text file containing the ids
    url = "https://raw.githubusercontent.com/ModestSerhat/cs2-marketplace-ids/main/cs2_marketplaceids.json"

    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (non-2xx status codes)

        # Parse the response content
        return parse_response(response.json()['items'])

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while loading items id dictonary: {e}")

def parse_response(content):
    id_dict = {}
    for item in content:
        try:
            item_buff_id = content[item]['buff163_goods_id']
        except:
            None
        try:
            item_youpin_id = content[item]['youpin_id']
        except:
            item_youpin_id = None
        item_name = item
        cleaned_key = clear_item_name(item_name)
        id_dict[cleaned_key] = int(item_buff_id)

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

