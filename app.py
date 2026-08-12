import gradio as gr
import pandas as pd
from huggingface_hub import InferenceClient

#from step 1 of lesson 12
from sentence_transformers import SentenceTransformer
import torch

business_df = pd.read_json("yelp_academic_dataset_business.json", lines=True)
# Fill missing values so string concatenation doesn't break
for col in ["name", "city", "categories"]:
    business_df[col] = business_df[col].fillna("")

#to filter to actual restaurants/food places only,since the business file includes every kind of business (dentists, salons, etc.)
business_df = business_df[business_df["categories"].str.contains("Restaurant|Food", case=False, na=False)].copy()

#for restaurants in the file that don't have any ratings
business_df["stars"] = business_df["stars"].fillna("No rating available")

business_df["chunk_text"] = (
    "Restaurant: " + business_df["name"] +
    " | City: " + business_df["city"] +
    " | Categories: " + business_df["categories"] +
    " | Rating: " + business_df["stars"].astype(str)
)
business_df["chunk_text"] = business_df["chunk_text"].str.replace("\n", " ", regex=False)
northstar_text = "\n".join(business_df["chunk_text"].astype(str).tolist())

def preprocess_text(text):
  # Strip extra whitespace from the beginning and the end of the text
  cleaned_text = text.strip()
  # Split the cleaned_text by every newline character (\n)
  chunks = cleaned_text.split("\n")
  # Create an empty list to store cleaned chunks
  cleaned_chunks = []
  # Write your for-in loop below to clean each chunk and add it to the cleaned_chunks list
  # This is only one way scholars may write this, but there are other ways!
  for chunk in chunks:
    stripped_chunk = chunk.strip()
    if len(stripped_chunk) > 0:
      cleaned_chunks.append(stripped_chunk)
  # The if chunk.strip() conditional is truthy if the string is not empty
  # cleaned_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
  # Return the cleaned_chunks
  return cleaned_chunks

cleaned_chunks = preprocess_text(northstar_text)
#step 4 from lesson 12
# Load the pre-trained embedding model that converts text to vectors
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embeddings(text_chunks):
  # Convert each text chunk into a vector embedding and store as a tensor
  chunk_embeddings = model.encode(text_chunks, convert_to_tensor=True) # Replace ... with the cleaned_chunks list
  # Return the chunk_embeddings
  return chunk_embeddings

# Call the create_embeddings function and store the result in a new chunk_embeddings variable
chunk_embeddings = create_embeddings(cleaned_chunks) # Complete this line

#step 5 from lesson 12
# Define a function to find the most relevant text chunks for a given query, chunk_embeddings, and text_chunks
def get_top_chunks(query, chunk_embeddings, text_chunks):
  # Convert the query text into a vector embedding
  query_embedding = model.encode(query, convert_to_tensor=True) # Complete this line
  # Normalize the query embedding to unit length for accurate similarity comparison
  query_embedding_normalized = query_embedding / query_embedding.norm()
  # Normalize all chunk embeddings to unit length for consistent comparison
  chunk_embeddings_normalized = chunk_embeddings / chunk_embeddings.norm(dim=1, keepdim=True)
  # Calculate cosine similarity between all chunks and the query using matrix multiplication
  similarities = torch.matmul(chunk_embeddings_normalized, query_embedding_normalized) # Complete this line
  # Find the indices of the 3 chunks with highest similarity scores
  top_indices = torch.topk(similarities, k=3).indices
  # Create an empty list to store the most relevant chunks
  top_chunks = []
  # Loop through the top indices and retrieve the corresponding text chunks
  for i in top_indices:
    chunk = text_chunks[i]
    top_chunks.append(chunk)

  # Return the list of most relevant chunks
  return top_chunks

client = InferenceClient("Qwen/Qwen2.5-7B-Instruct", bill_to="kode-with-klossy")

def respond(message,history): #defining what happenes every time a user types a message and hits enter
    northstar_chunks = get_top_chunks(message, chunk_embeddings, cleaned_chunks)    
    system_instruction = (
        f"You are NorthStar*, a friendly AI travel guide specializing in food recommendations.\n Ask the user for three things if they haven't provided them:\n 1) Where they are going (City/Location)\n 2) Their budget/price range ($, $$, or $$$)\n 3) The meal of the day (Breakfast, Brunch, Lunch, Dinner)\n Structure your recommendations clearly with the restaurant name, why it fits their request, and a tip on what to order. Make sure to pull from: {northstar_chunks}"
    )
    #managing the conversation memory
    messages = [{"role":"system","content": system_instruction}]

    #include past conversation logs
    if history:
        messages.extend(history)

    #include the current user message
    messages.append({"role":"user","content":message})
    
    #get the answer and launching the app
    response = client.chat_completion(messages, max_tokens=200, temperature=0.8)
    return response.choices[0].message.content.strip()

chatbot = gr.ChatInterface(respond)
chatbot.launch()

