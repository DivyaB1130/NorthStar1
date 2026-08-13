import gradio as gr
import os
import requests
import re

# ============================================================
# FOURSQUARE
# ============================================================

FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY")

FOURSQUARE_URL = "https://places-api.foursquare.com/places/search"


# ============================================================
# GET RESTAURANTS FROM FOURSQUARE
# ============================================================

def get_restaurants(location):

    if not location:
        return []

    headers = {
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
        "Accept": "application/json",
        "X-Places-Api-Version": "2025-06-17"
    }

    params = {
        "near": location.strip(),
        "fsq_category_ids": "13065,13032,13002,13145,13054,13040,13052,13053",
        "fields": "name,location,categories,price",
        "limit": 50
    }

    try:
        response = requests.get(
            FOURSQUARE_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 429:
            return []

        response.raise_for_status()

        results = response.json().get("results", [])

        restaurants = []

        for place in results:

            name = place.get("name", "Unknown")

            address = place.get(
                "location", {}
            ).get(
                "formatted_address",
                "Address not listed"
            )

            categories = [
                c.get("name", "")
                for c in place.get("categories", [])
            ]

            category_text = ", ".join(categories)

            price = place.get("price")

            restaurants.append({
                "name": name,
                "address": address,
                "categories": category_text,
                "price": price
            })

        return restaurants

    except Exception as e:
        print("Foursquare error:", e)
        return []


# ============================================================
# FILTER RESTAURANTS
# ============================================================

def get_recommendations(location, meal, price, cuisine, dietary, vibe):

    restaurants = get_restaurants(location)

    if not restaurants:
        return []

    results = restaurants.copy()

    # ========================================================
    # PRICE
    # ========================================================

    if price:

        price_map = {
            "$": 1,
            "$$": 2,
            "$$$": 3,
            "$$$$": 4
        }

        wanted_price = price_map.get(price)

        if wanted_price:
            results = [
                r for r in results
                if r["price"] == wanted_price
            ]


    # ========================================================
    # CUISINE
    # ========================================================

    if cuisine and cuisine != "Surprise Me":

        cuisine_keywords = {

            "Asian": [
                "asian",
                "chinese",
                "japanese",
                "thai",
                "indian",
                "korean",
                "vietnamese",
                "sushi",
                "ramen",
                "filipino"
            ],

            "Italian": [
                "italian",
                "pizza",
                "pasta"
            ],

            "Mexican": [
                "mexican",
                "taco",
                "tex-mex"
            ],

            "American": [
                "american",
                "burger",
                "bbq",
                "steak"
            ],

            "Healthy": [
                "healthy",
                "salad",
                "vegan",
                "vegetarian",
                "mediterranean"
            ]
        }

        keywords = cuisine_keywords.get(cuisine, [])

        filtered = []

        for restaurant in results:

            text = (
                restaurant["name"]
                + " "
                + restaurant["categories"]
            ).lower()

            if any(keyword in text for keyword in keywords):
                filtered.append(restaurant)

        results = filtered


    # ========================================================
    # MEAL
    # ========================================================

    if meal:

        meal_keywords = {

            "Breakfast": [
                "breakfast",
                "brunch",
                "cafe",
                "coffee",
                "bakery"
            ],

            "Lunch": [
                "lunch",
                "sandwich",
                "deli",
                "cafe",
                "restaurant"
            ],

            "Dinner": [
                "restaurant",
                "steak",
                "italian",
                "mexican",
                "japanese",
                "bar"
            ],

            "Late Night": [
                "bar",
                "pub",
                "night",
                "pizza",
                "fast food"
            ]
        }

        keywords = meal_keywords.get(meal, [])

        filtered = []

        for restaurant in results:

            text = (
                restaurant["name"]
                + " "
                + restaurant["categories"]
            ).lower()

            if any(keyword in text for keyword in keywords):
                filtered.append(restaurant)

        # Only use the meal filter if it actually finds something.
        # This prevents cities from showing "No matches" too easily.
        if filtered:
            results = filtered


    # ========================================================
    # VIBE
    # ========================================================

    if vibe:

        vibe_keywords = {

            "Quick & Casual": [
                "fast food",
                "takeout",
                "deli",
                "sandwich",
                "cafe"
            ],

            "Sit-down": [
                "restaurant",
                "bistro",
                "steakhouse",
                "italian",
                "mexican"
            ],

            "Special Occasion": [
                "steakhouse",
                "fine dining",
                "wine",
                "restaurant"
            ],

            "Café / Relaxed": [
                "cafe",
                "coffee",
                "bakery",
                "tea"
            ],

            "Fun & Social": [
                "bar",
                "pub",
                "brewery",
                "sports bar"
            ]
        }

        keywords = vibe_keywords.get(vibe, [])

        filtered = []

        for restaurant in results:

            text = (
                restaurant["name"]
                + " "
                + restaurant["categories"]
            ).lower()

            if any(keyword in text for keyword in keywords):
                filtered.append(restaurant)

        # Same idea here:
        # only apply vibe if it produces results.
        if filtered:
            results = filtered


    # ========================================================
    # DIETARY
    # ========================================================

    if dietary:

        dietary_keywords = []

        for item in dietary:

            if item == "Vegetarian":
                dietary_keywords += [
                    "vegetarian",
                    "vegan"
                ]

            elif item == "Vegan":
                dietary_keywords += [
                    "vegan"
                ]

            elif item == "Halal":
                dietary_keywords += [
                    "halal"
                ]

            elif item == "Gluten-Free":
                dietary_keywords += [
                    "gluten free",
                    "gluten-free"
                ]

        filtered = []

        for restaurant in results:

            text = (
                restaurant["name"]
                + " "
                + restaurant["categories"]
            ).lower()

            if any(keyword in text for keyword in dietary_keywords):
                filtered.append(restaurant)

        # Only filter if Foursquare actually has matches.
        if filtered:
            results = filtered


    return results[:10]


# ============================================================
# FILTER SUMMARY
# ============================================================

def build_filter_summary_html(
    location,
    meal,
    price,
    cuisine,
    dietary,
    vibe
):

    dietary_text = (
        ", ".join(dietary)
        if dietary
        else "No dietary restrictions"
    )

    preferences = []

    if meal:
        preferences.append(meal)

    if price:
        preferences.append(price)

    if cuisine:
        preferences.append(cuisine)

    if vibe:
        preferences.append(vibe)

    preference_text = (
        " — ".join(preferences)
        if preferences
        else "No preferences set"
    )

    return f"""
    <div class="filter-summary">
        <p>📍 {location or "Anywhere"}</p>
        <p>{preference_text}</p>
        <p>{dietary_text}</p>
    </div>
    """


# ============================================================
# BUILD RESULTS
# ============================================================

def build_results_html(
    location,
    meal,
    price,
    cuisine,
    dietary,
    vibe
):

    restaurants = get_recommendations(
        location,
        meal,
        price,
        cuisine,
        dietary,
        vibe
    )

    if not restaurants:

        return """
        <p class="no-results">
            No matches found — try changing your filters.
        </p>
        """

    cards = ""

    for restaurant in restaurants:

        price_display = ""

        if restaurant["price"]:
            price_display = "$" * restaurant["price"]

        else:
            price_display = "$$"

        cards += f"""
        <div class="result-card">

            <h3>{restaurant["name"]}</h3>

            <p class="result-meta">
                {price_display}
            </p>

            <p class="result-address">
                📍 {restaurant["address"]}
            </p>

            <p class="result-tagline">
                {restaurant["categories"]}
            </p>

        </div>
        """

    return cards


# ============================================================
# BUTTON FUNCTIONS
# ============================================================

def handle_find_food(
    location,
    meal,
    price,
    cuisine,
    dietary,
    vibe
):

    summary = build_filter_summary_html(
        location,
        meal,
        price,
        cuisine,
        dietary,
        vibe
    )

    results = build_results_html(
        location,
        meal,
        price,
        cuisine,
        dietary,
        vibe
    )

    return (
        gr.update(visible=False),
        gr.update(visible=True),
        summary,
        results
    )


def handle_edit_filters():

    return (
        gr.update(visible=True),
        gr.update(visible=False)
    )


# ============================================================
# CSS
# ============================================================

custom_css = """

body,
.gradio-container {
    background-color: #C9A9A6 !important;
}

#header {
    text-align: center;
    background-color: #183B35 !important;
    color: #FAF1E6 !important;
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 25px;
}

#header h1,
#header p {
    color: #FAF1E6 !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #183B35 !important;
}

#location-box {
    background-color: #183B35 !important;
    border-radius: 20px !important;
    padding: 20px !important;
}

#location-box input {
    background-color: #041D47 !important;
    border: 2px solid #FAF1E6 !important;
    color: #FAF1E6 !important;
}

#location-box input::placeholder {
    color: #C9A9A6 !important;
}

#preferences-group {
    background-color: #183B35 !important;
    border-radius: 12px !important;
    padding: 15px !important;
}

#preferences-group .form,
#preferences-group .block {
    background-color: #183B35 !important;
    border: none !important;
}

#meal-radio,
#price-radio,
#cuisine-radio,
#dietary-checkbox,
#vibe-radio {
    background-color: transparent !important;
    padding: 10px 0 !important;
}

#meal-radio label,
#price-radio label,
#cuisine-radio label,
#vibe-radio label,
#dietary-checkbox label {
    background-color: #5B2333 !important;
    color: #FAF1E6 !important;
    border-radius: 10px !important;
    border: 2px solid #5B2333 !important;
    padding: 10px 15px !important;
}

#meal-radio label span,
#price-radio label span,
#cuisine-radio label span,
#vibe-radio label span,
#dietary-checkbox label span {
    color: #FAF1E6 !important;
}

#meal-radio label:has(input:checked),
#price-radio label:has(input:checked),
#cuisine-radio label:has(input:checked),
#vibe-radio label:has(input:checked),
#dietary-checkbox label:has(input:checked) {
    background-color: #4E7360 !important;
    border-color: #4E7360 !important;
}

label {
    color: #183B35 !important;
}

#find-button {
    background-color: #5B2333 !important;
    color: #FAF1E6 !important;
    font-size: 18px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 15px !important;
}

#find-button:hover {
    background-color: #183B35 !important;
}

#results-header-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 20px !important;
}

#results-header-row h2 {
    margin: 0 !important;
}

#edit-filters-button {
    background-color: #5B2333 !important;
    color: #FAF1E6 !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 18px !important;
}

#edit-filters-button:hover {
    background-color: #183B35 !important;
}

.filter-summary {
    background-color: #183B35 !important;
    color: #FAF1E6 !important;
    border-radius: 12px !important;
    padding: 15px 20px !important;
    margin-bottom: 20px !important;
}

.filter-summary p {
    margin: 4px 0 !important;
    color: #FAF1E6 !important;
}

.result-card {
    background-color: #FAF1E6 !important;
    color: #183B35 !important;
    border-radius: 15px !important;
    padding: 20px !important;
    margin-bottom: 18px !important;
    border: 2px solid #4E7360 !important;
}

.result-card h3 {
    margin-top: 0 !important;
    color: #183B35 !important;
}

.result-meta {
    color: #5B2333 !important;
    font-weight: bold !important;
}

.result-address {
    color: #183B35 !important;
}

.result-tagline {
    font-style: italic !important;
    color: #183B35 !important;
}

.no-results {
    color: #183B35 !important;
    text-align: center !important;
    padding: 20px !important;
}

"""


# ============================================================
# GRADIO APP
# ============================================================

with gr.Blocks(
    css=custom_css,
    title="NorthStar*"
) as demo:

    # ========================================================
    # HEADER
    # ========================================================

    gr.Markdown(
        """
        <div id="header">
            <h1>★ NORTHSTAR*</h1>
            <p>FOOD GUIDED BY YOU</p>
            <p>Find your next favorite bite.</p>
        </div>
        """,
        elem_id="header"
    )


    # ========================================================
    # SCREEN 1
    # ========================================================

    with gr.Column(
        visible=True,
        elem_id="screen1"
    ) as screen1:

        gr.Markdown("## Where are you eating?")

        location = gr.Textbox(
            label="📍 Location",
            placeholder="Search a city, neighborhood, or destination...",
            elem_id="location-box"
        )

        gr.Markdown("## What are you looking for?")

        with gr.Group(
            elem_id="preferences-group"
        ):

            meal = gr.Radio(
                [
                    "Breakfast",
                    "Lunch",
                    "Dinner",
                    "Late Night"
                ],
                label="🍽️ Meal",
                elem_id="meal-radio"
            )

            price = gr.Radio(
                [
                    "$",
                    "$$",
                    "$$$",
                    "$$$$"
                ],
                label="💰 Price Range",
                elem_id="price-radio"
            )

            cuisine = gr.Radio(
                [
                    "Asian",
                    "Italian",
                    "Mexican",
                    "Healthy",
                    "American",
                    "Surprise Me"
                ],
                label="🥗 Cuisine",
                elem_id="cuisine-radio"
            )

            dietary = gr.CheckboxGroup(
                [
                    "Vegetarian",
                    "Vegan",
                    "Halal",
                    "Gluten-Free"
                ],
                label="🥒 Dietary Preferences (Optional)",
                elem_id="dietary-checkbox"
            )

            vibe = gr.Radio(
                [
                    "Quick & Casual",
                    "Sit-down",
                    "Special Occasion",
                    "Café / Relaxed",
                    "Fun & Social"
                ],
                label="✨ Dining Vibe",
                elem_id="vibe-radio"
            )

        find_button = gr.Button(
            "FIND MY FOOD →",
            elem_id="find-button"
        )


    # ========================================================
    # SCREEN 2
    # ========================================================

    with gr.Column(
        visible=False,
        elem_id="screen2"
    ) as screen2:

        with gr.Row(
            elem_id="results-header-row"
        ):

            gr.Markdown("## ← NorthStar*")

            edit_filters_button = gr.Button(
                "★ Edit Filters",
                elem_id="edit-filters-button"
            )

        filter_summary_display = gr.HTML()

        gr.Markdown(
            "## Here's what I found for you!!"
        )

        results_display = gr.HTML()


    # ========================================================
    # WIRING
    # ========================================================

    find_button.click(
        fn=handle_find_food,
        inputs=[
            location,
            meal,
            price,
            cuisine,
            dietary,
            vibe
        ],
        outputs=[
            screen1,
            screen2,
            filter_summary_display,
            results_display
        ]
    )

    edit_filters_button.click(
        fn=handle_edit_filters,
        inputs=[],
        outputs=[
            screen1,
            screen2
        ]
    )


# ============================================================
# LAUNCH
# ============================================================

demo.launch()