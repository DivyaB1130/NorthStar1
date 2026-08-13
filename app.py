import gradio as gr
import os
from huggingface_hub import InferenceClient
FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY")

def extract_preferences(message):
    extraction_prompt = (
        "Extract the following from the user's message and return ONLY valid JSON.\n"
        "Fields: destination_city (string or null), current_location (string or null), price (integer 1-4 or null), meal (string or null),"
        "intent (one of: \"food\", \"activities\", or null if unclear).\n\n"
        f"User message: \"{message}\"\n\nJSON:"
    )
    
    response = client.chat_completion([{"role": "user", "content": extraction_prompt}])
    raw = response.choices[0].message.content.strip()
    try: #trying to covert the reply into a dictionary  
        preferences = json.loads(raw)
  #if for any reason it doesn't covert, fall back to default(all fields empty) so the whole code doesn't stop
    except json.JSONDecodeError:
        preferences = {"destination_city": None, "price": None, "meal": None} 
    return preferences

def get_food_recommendations(city, price=None, limit=30):
    url = "https://places-api.foursquare.com/places/search"
    headers = {#identifies us when we go to the url
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
        "Accept": "application/json",
        "X-Places-Api-Version": "2025-06-17"
    }
    '''
13065 — Restaurant (covers every restaurant sub-type), 13032 — Café / Coffee House, 13002 — Bakery, 13054 — Food Truck, 13040 — Dessert Shop
13052 — Food Court, 13053 — Food Stand)
    '''
    params = {#paramenters for the search
        "near": city,
        "fsq_category_ids": "13065,13032,13002,13145,13054,13040,13052,13053",
        "fields": "name,location,categories,price",
        "limit": limit,
    }
    if price:
        params["min_price"] = price
        params["max_price"] = price

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 429:#lets us know if there have beeen too many pull requests instead of just crashing
        print("Rate limited — wait a bit before trying again.")
        return []

    response.raise_for_status()
    results = response.json().get("results", [])

    chunks = []
    for place in results: #organising all the info we got
        name = place.get("name", "Unknown")
        address = place.get("location", {}).get("formatted_address", "Address not listed")
        category = ", ".join(c["name"] for c in place.get("categories", []))
        place_price = place.get("price", "Price not listed")
        chunks.append(f"Restaurant: {name} | Address: {address} | Categories: {category} | Price: {place_price}")
   
    return chunks

def get_activity_recommendations(city, limit=30):
    url = "https://places-api.foursquare.com/places/search"
    headers = { #identifies us when we vist the url to pull info
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
        "Accept": "application/json",
        "X-Places-Api-Version": "2025-06-17"
    }
    '''
foursquare category ids: 10000 -	Arts and Entertainment, 16000 - Landmarks and Outdoors, 18000- Sports and Recreation, 
19000 - Travel and Transportation, 17116 - Souvenir Store, 17144 - Market, 17115 - Shopping Plaza, 17089 - Gift Store.
    '''
    params = {#the parameters for the search we want to do
        "near": city,
        "fsq_category_ids": "10000,16000,18000,19000,17116,17144,17115,17089,17002,17138,17018",
        "fields": "name,location,categories,price",
        "limit": limit,
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 429: #if there have been too many pull requests
        print("Rate limited — wait a bit before trying again.")
        return []
    response.raise_for_status()
    results = response.json().get("results", [])

    chunks = []
    for place in results: #organising all the info we got
        name = place.get("name", "Unknown")
        address = place.get("location", {}).get("formatted_address", "Address not listed")
        category = ", ".join(c["name"] for c in place.get("categories", []))
        place_price = place.get("price", "Price not listed")
        chunks.append(f"Attraction: {name} | Address: {address} | Categories: {category} | Price: {place_price} ")

    return chunks

client = InferenceClient("Qwen/Qwen2.5-7B-Instruct", bill_to="kode-with-klossy")

def respond(message,history): 
    preferences = extract_preferences(message)    
    if not preferences.get("destination_city"):
        northstar_chunks = []
    elif preferences.get("intent") == "activities":
        northstar_chunks = get_activity_recommendations(city=preferences["destination_city"])
    else:
        # default to food if intent is food or unclear
        northstar_chunks = get_food_recommendations(city=preferences["destination_city"],price=preferences.get("price"))
        
    system_instruction = (f"You are NorthStar*, a friendly AI travel guide for food and activities. The user is looking for: {preferences.get('meal', 'a meal')}." 
        "From the places listed below, prioritize and highlight the ones that genuinely make sense for that time of day (e.g., a coffee shop or bakery fits breakfast better than a steakhouse)."
        "Structure your recommendations clearly with the address, why they fit the user's request, and some tips on what to order"
        f"Here is live data to pull from: {northstar_chunks}.")
    #managing the conversation memory
    messages = [{"role":"system","content": system_instruction}]

    #include past conversation logs
    if history:
        messages.extend(history)

    #include the current user message
    messages.append({"role":"user","content":message})
    
    #get the answer and launching the app
    response = client.chat_completion(messages, max_tokens=200, temperature=0.3)
    return response.choices[0].message.content.strip()

chatbot = gr.ChatInterface(
    respond,
    title="NorthStar",
    description="Hi! I'm NorthStar — your guide to finding great food and things to do wherever you're headed. What are you in the mood for?",
    examples=["I'm craving some food", "I want to explore somewhere new"]
)
chatbot.launch()

