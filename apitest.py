import requests

def access_api_and_analyze(cookie_data, goods_id):
    url = f"https://buff.163.com/api/market/goods/price_history/buff?game=csgo&goods_id={goods_id}&currency=BRL&days=30&buff_price_type=1&with_sell_num=false"

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
    last_two_prices = last_prices[-2:]
    mean_last_two_prices = sum(price[1] for price in last_two_prices) / 2

    # Get the last 15 prices (17 - 2)
    mean_prices = last_prices[:-2]

    # Get the mean of the last 15 prices
    mean_last_15_prices = sum(price[1] for price in mean_prices) / len(mean_prices)

    # Check if the most recent price is 10% higher than the mean of the last 15 prices
    print("\n", mean_last_15_prices, mean_last_two_prices)
    return (mean_last_two_prices > mean_last_15_prices*1.10)

# Your cookie data
cookie_data = "Device-Id=ncG8AGHQEmTmluQTcgQl; Locale-Supported=en; game=csgo; to_steam_processing_click230405T17900125601=1; to_steam_processing_click230408T17915539961=1; to_steam_processing_click230408T17909896951=1; r_ntcid=730:155; to_steam_processing_click230411T18295587641=1; to_steam_processing_click230411T18295877081=1; to_steam_processing_click230414T18336081151=1; to_steam_processing_click230416T18377675391=1; to_steam_processing_click230417T18391009451=1; to_steam_processing_click230417T18391745471=1; to_steam_processing_click230420T18425400661=1; to_steam_processing_click230502T18261245701=1; to_steam_processing_click230505T18639240771=1; to_steam_processing_click230505T18639806881=1; to_steam_processing_click230515T18763682791=1; NTES_YD_SESS=nMo4eScneyoP7faPIGZoEzFAV_0ndjxX5aLvbWGoeWlpuES28aY.ohRetXKgBIGEMW4qXvJ8zGUNYiMvA.IYIHL1C6R57YkukJV0VyRJEvg1.8wa22AeYTRiVtbypsDpepIfnWnD.S6NNu75LIdPiA73D8.Xrq07np0s_zDOdz1pPynYgWmNnM9alwhd0LAmKfOefPiQDz4cgQhqfLESVuqOq9vJMKX3AR0M7tnOpzGchj0xF0MFrDR.s; S_INFO=1695262065|0|0&60##|55-21999490866; P_INFO=55-21999490866|1695262065|1|netease_buff|00&99|null&null&null#BR&null#10#0|&0||55-21999490866; steam_verify_result=; session=1-LAn_2nT8V7FpA16-qTfH_8avcPvH9Hm9_i76wNzwVERZ2036662111; csrf_token=IjFjNjNlMjg4NTg3YTlmZTZiMDExMDU4YzY5NmJhYTAxNDJlMGZiN2Ui.GJ1uaQ.4WjQbLL3E36Ku0S3i7GaVkE4PGc"  # Your cookie data here

# Goods ID you want to query
goods_id_to_query = 35416

# Check if the price has exploded recently
result = access_api_and_analyze(cookie_data, goods_id_to_query)
if result:
    print("True")
else:
    print("False")

