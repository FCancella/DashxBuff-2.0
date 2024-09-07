from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd

# Modules
from cny2brl import cny_brl_rate
from buff_skins_id import load_id_dict, all_items_data_dict, clear_item_name, check_item_dash_qnt#, access_api_with_cookies
from auxiliary import loading_bar

import requests
import sys
import concurrent.futures
#from bs4 import BeautifulSoup

# Record the start time
start_time = time.time()

# Change the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Call the function to get the Yuan to Brazilian Real exchange rate
yuan_brl_rate = cny_brl_rate()
print("* CNY/BRL rate successfully updated!")

options = webdriver.ChromeOptions()
options.add_argument("--blink-settings=imagesEnabled=false") # Disable images
options.add_argument("--disable-features=CSSStyleSheet") # Disable CSS styles
options.add_argument('--headless') # Run in headless mode (without a graphical user interface)
options.add_argument("--disable-logging")  # Disable logging for DevTools
driver = webdriver.Chrome(options=options)

# Define panda's display options 
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


price_min = 10
price_max = 6000

#checked = 8
qnt_checked = 25

#cookie_data = "Device-Id=ncG8AGHQEmTmluQTcgQl; Locale-Supported=en; game=csgo; to_steam_processing_click230405T17900125601=1; to_steam_processing_click230408T17915539961=1; to_steam_processing_click230408T17909896951=1; r_ntcid=730:155; to_steam_processing_click230411T18295587641=1; to_steam_processing_click230411T18295877081=1; to_steam_processing_click230414T18336081151=1; to_steam_processing_click230416T18377675391=1; to_steam_processing_click230417T18391009451=1; to_steam_processing_click230417T18391745471=1; to_steam_processing_click230420T18425400661=1; to_steam_processing_click230502T18261245701=1; to_steam_processing_click230505T18639240771=1; to_steam_processing_click230505T18639806881=1; to_steam_processing_click230515T18763682791=1; NTES_YD_SESS=nMo4eScneyoP7faPIGZoEzFAV_0ndjxX5aLvbWGoeWlpuES28aY.ohRetXKgBIGEMW4qXvJ8zGUNYiMvA.IYIHL1C6R57YkukJV0VyRJEvg1.8wa22AeYTRiVtbypsDpepIfnWnD.S6NNu75LIdPiA73D8.Xrq07np0s_zDOdz1pPynYgWmNnM9alwhd0LAmKfOefPiQDz4cgQhqfLESVuqOq9vJMKX3AR0M7tnOpzGchj0xF0MFrDR.s; S_INFO=1695262065|0|0&60##|55-21999490866; P_INFO=55-21999490866|1695262065|1|netease_buff|00&99|null&null&null#BR&null#10#0|&0||55-21999490866; steam_verify_result=; session=1-LAn_2nT8V7FpA16-qTfH_8avcPvH9Hm9_i76wNzwVERZ2036662111; csrf_token=IjFjNjNlMjg4NTg3YTlmZTZiMDExMDU4YzY5NmJhYTAxNDJlMGZiN2Ui.GJ1uaQ.4WjQbLL3E36Ku0S3i7GaVkE4PGc"


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


items_info_dict = all_items_data_dict()
'''
items_info_dict = {
id1: [30d, 7d, 24h],
id2: [30d, 7d, 24h],
id3: [30d, 7d, 24h],
}
'''
print("* Items info (steam) dictionary successfully loaded")

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

print("\nScraping all DASHSKINS items")

################################################################################################################################################################
# # Iterate over each page of Dash Skins
# for page_num in range(1, page_limit+1):

#     url = base_url.format(page_num)

#     # Make the HTTP request and get the content
#     response = requests.get(url)

#     # Check if the request was successful (status code 200)
#     if response.status_code == 200:
#         # Parse the HTML content with BeautifulSoup
#         soup = BeautifulSoup(response.text, 'html.parser')

#         # Find all <div> elements with the specified class
#         div_tags = soup.find_all('div', class_='column is-2-fullhd is-3-widescreen is-4-desktop is-6-tablet is-12-mobile')

#         if not div_tags:
#             break

#         # Loop through the found <div> elements and extract the desired information
#         for div_tag in div_tags:

#             item_counter+=1

#             # Get the href attribute from the first <a> element
#             a_tag = div_tag.find('a')
#             if a_tag:
#                 href = a_tag.get('href')
#                 href_name = (href.split('/'))[2]
            
#             name = href_name.replace("-", " ")
         
#             # Get the text from the <span> element within the <div> with class "title ..."
#             title_div = div_tag.find('div', class_='title is-size-6 has-text-white-bis has-text-centered')
#             if title_div:
#                 span_text = (title_div.find_all('span'))[-1].text

#             # Remove "." (thousands separator in the pt-BR format)
#             # Replace "," with "." ("," represents decimal places in the pt-BR format)
#             price = float(re.findall(r"\d+\.?\d*", (span_text.replace(".","")).replace(",", "."))[0]) # e.g.: R$1.234,56 -> 1234.56

#             #print(f"{item_counter:4} | {name} - {price}")
#             loading_bar(item_counter, (int(page_limit-0.5))*120)

#             # Skip if item is a case key (not available on buff)
#             if "case key" in name:
#                 continue

# ################################################################################
#             #Skip if item has <1000 sells on 30days

#             # Get the item's Buff ID
#             item_id = id_dict.get(name.replace(" ",""))


#             # Check if the item_id is in the dictionary
#             if item_id in items_info_dict:
#                 try:
#                     # Access the 'sold' variable on '30_days' for the specified item_id
#                     item_30d_sold_qnt = int(items_info_dict[item_id]['price'].get('30_days', {}).get('sold'))
#                 except:
#                     item_30d_sold_qnt = 0
#             else:
#                 item_30d_sold_qnt = 0

#             # Steam's sold quantity was the only way to measure the selling power of each items.
#             # > 3000 in 30d should equal +500 on buff
#             if item_30d_sold_qnt < 1000:
#                 continue
# ################################################################################
            
#             # Check if the item qualifies for the items list
#             if name in products and price >= products[name]:
#                     # Skip this item as it's more expensive than the one already seen
#                     continue
            
#             # Add/Update the item on the dictionary of viewed items
#             products[name] = price
################################################################################################################################################################

print("* Initializing DashSkins api analysis")
dash_api_url = f"https://api.dashskins.gg/v1/item?pageSize=100000&maxPriceBRL={price_max}&minPriceBRL={price_min}&sort=discount-desc"

# Send a GET request to the API
response = requests.get(dash_api_url)
response.raise_for_status()  # Raise an exception for bad responses (non-2xx status codes)

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
        
        ################################################################################
        #Skip if item has <1000 sells on 30days

        # Get the item's Buff ID
        item_id = id_dict.get(cleared_name)


        # Check if the item_id is in the dictionary
        if item_id in items_info_dict:
            try:
                # Access the 'sold' variable on '30_days' for the specified item_id
                item_30d_sold_qnt = int(items_info_dict[item_id][1][0])
                #item_7d_sold_qnt = int(items_info_dict[item_id][1][1])
                #item_24h_sold_qnt = int(items_info_dict[item_id][1][2])
            except:
                print(f"* error. Failed item - {name}")
                item_30d_sold_qnt = 0
        else:
            print(f"* error. Item not found in dictionary - {name} - Dash: {price}")
            item_30d_sold_qnt = 0 

        '''
        # Steam's sold quantity was the only way to measure the selling power of each item.
        if item_30d_sold_qnt < 1000:
            continue
        '''
        ################################################################################

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

print("\nScraping and analysing selected (+1000, no repeat) items")

# Define a function to process a single product
def process_product(product_name):
    global item_counter, qnt_checked #, checked, cookie_data

    item_counter+=1
    loading_bar(item_counter, total_items)

    formated_product_name = clear_item_name(product_name)

################################################################################
    # Get the item's Buff ID
    item_id = id_dict.get(formated_product_name)

    # Check if the item_id is in the dictionary
    if item_id in items_info_dict:
        try:
            # Access the 'sold' variable on '30_days' for the specified item_id
            item_30d_sold_qnt = int(items_info_dict[item_id][1][0])
        except:
            item_30d_sold_qnt = 0
    else:
        item_30d_sold_qnt = 0

    # Steam's sold quantity was the only way to measure the selling power of each items.
    # > 3000 in 30d should equal +500 on buff
################################################################################
        
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

    # item_30d_sold_qnt > 1000 and
    if (buff_offers >= 91 and diff > 2 and dash_price >= 4.99) or \
        (item_30d_sold_qnt > 4000 and \
        buff_offers >= 91 and diff < -15 and \
        dash_price/buff_price <= 3 and \
        # Price difference can't be >300% (unreal)
        "Sticker" not in product_name):

        '''
        # Checking first 4 items price trend (Check if price exploded)
        if diff > 2 and checked > 0:
            exploded_bool = access_api_with_cookies(cookie_data, item_id)
            if exploded_bool:
                product_name = product_name + " FAILED"
            else:
                product_name = product_name + " PASSED"

            print(product_name, dash_price, buff_price, diff, buff_offers, item_30d_sold_qnt)
            checked -= 1
        '''
        

        '''
        if qnt_checked >= 0 and diff < 0:
            item_dash_qnt = check_item_dash_qnt(product_name)
            qnt_checked -= 1
        else:
            item_dash_qnt = "N/A"
        '''

        # Adiciona uma nova linha ao dataframe com as informações do produto
        #linha.append([product_name, dash_price, buff_price, diff, buff_offers, item_dash_qnt, item_30d_sold_qnt])
        linha.append([product_name, dash_price, buff_price, diff, buff_offers, item_30d_sold_qnt])

# Create a ThreadPoolExecutor with 2 concurrent threads ( More than 2 usually equals API errors)
with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
    # Use the executor to process products concurrently
    results = list(executor.map(process_product, products.keys()))



driver.quit()

print("\n\nITEMS\n\n")

# Sort the list based on the "diff" field (4th element in each sublist)
sorted_linha = sorted(linha, key=lambda x: x[3], reverse=True)

# Create a DataFrame from the sorted list
#df = pd.DataFrame(sorted_linha, columns=["Product Name", "Dash Price", "Buff Price", "Diff", "Buff Offers", "Dash Offers", "Steam 30d Offers"])
df = pd.DataFrame(sorted_linha, columns=["Product Name", "Dash Price", "Buff Price", "Diff", "Buff Offers", "Steam 30d Offers"])

# Save the DataFrame as a CSV file
df.to_csv("skins.csv", index=False)

# Print the DataFrame (optional)
print(df)

stop_time = time.time()
elapsed_time = stop_time - start_time
print(f"Elapsed Time: {elapsed_time} seconds")
