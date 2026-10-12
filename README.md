# NorthStar* (capstone)

**Food guided by you.** NorthStar is an AI travel-guide chatbot that recommends real places to eat and things to do in any city, without making places up.

Capstone project for Kode With Klossy's 2026 AI & Machine Learning program (Camp 4.3, Group C4). This repository holds the full development history of the deployed app.

**Try it:** [huggingface.co/spaces/kode-with-klossy/4.3-groupC4-capstone](https://huggingface.co/spaces/kode-with-klossy/4.3-groupC4-capstone)

## How it works

NorthStar uses retrieval-augmented generation (RAG):

1. **Understand the request.** A large language model (Qwen 2.5, 7B Instruct, via Hugging Face Inference) turns a casual message into structured preferences: city, price, meal, food or activities, and whether the user wants more options.
2. **Retrieve real places.** The app pulls live places from the Foursquare Places API, caches results to avoid repeat calls, and falls back to a saved Yelp dataset when live data is unavailable.
3. **Answer from the data only.** Only the retrieved places are passed to the model, five at a time. The model is instructed never to invent a place, and to say so when it has no data.

Replies stream in, and the conversation remembers the city and request, so "show me more" pages through new options.

## Team

Divya Bhatia, Oluwatobi (Tobi) Adesanmi, Samyuktha Raja and Vishruti. Leen Attia and Kaitlyn Van Gorkom also contributed commits.

## Running it

```bash
pip install -r requirements.txt
export FOURSQUARE_API_KEY=your_key   # https://foursquare.com/developers
python app.py
```

Calls to the language model need a Hugging Face account. The `.parquet` and `yelp_academic_dataset_*.json` files here are Git LFS pointers to data stored with the Hugging Face Space; the Yelp data itself is not redistributed. Download the Yelp Open Dataset to run the fallback locally.

Built with Python, Gradio, Hugging Face and the Foursquare Places API.
