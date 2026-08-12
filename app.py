import gradio as gr
from huggingface_hub import InferenceClient

#from step 1 of lesson 12
from sentence_transformers import SentenceTransformer
import torch



#from step 2 of lesson 12
with open("northstar_rag_dataset.parquet","r",encoding="utf-8") as file:
    #read the entire contents of the file and store it in a variable
    northstar_text = file.read()

#print the text below
print(northstar_text)



#from step 3 of lesson 12
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

  # ===== SPICY CHALLENGE: LIST COMPREHENSION =====
  # The if chunk.strip() conditional is truthy if the string is not empty
  # cleaned_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

  # Print cleaned_chunks
  print(cleaned_chunks)

  # Print the length of cleaned_chunks
  print(len(cleaned_chunks))

  # Return the cleaned_chunks
  return cleaned_chunks

cleaned_chuncks = preprocess_text(northstar_text)



#step 4 from lesson 12
# Load the pre-trained embedding model that converts text to vectors
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embeddings(text_chunks):
  # Convert each text chunk into a vector embedding and store as a tensor
  chunk_embeddings = model.encode(text_chunks, convert_to_tensor=True) # Replace ... with the cleaned_chunks list

  # Print the chunk embeddings
  print(chunk_embeddings)

  # Print the shape of chunk_embeddings
  print(chunk_embeddings.shape)

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

  # Print the similarities
  print(similarities)

  # Find the indices of the 3 chunks with highest similarity scores
  top_indices = torch.topk(similarities, k=3).indices

  # Print the top indices
  print(top_indices)

  # Create an empty list to store the most relevant chunks
  top_chunks = []

  # Loop through the top indices and retrieve the corresponding text chunks
  # This is only one way scholars may write this, but there are other ways!
  for i in top_indices:
    chunk = text_chunks[i]
    top_chunks.append(chunk)

  # ===== SPICY CHALLENGE: LIST COMPREHENSION =====
  # top_chunks = [chunks[i] for i in top_indices]

  # Return the list of most relevant chunks
  return top_chunks


# This is the same pattern from the Generative AI lesson! It uses the
# Inference Provider API to send your messages to an AI model and get
# a response back. Swap out the model below for a different one if
# you want to experiment!
#
# Note: if this Space doesn't already have one, you'll need to add an
# HF_TOKEN secret in the Space's Settings tab for this to work
# (Settings -> Variables and secrets -> New secret).

client = InferenceClient("Qwen/Qwen2.5-7B-Instruct", bill_to="kode-with-klossy")

def respond(message,history): #defining what happenes every time a user types a message and hits enter
    northstar_chunks = get_top_chunks(message, chunk_embeddings, cleaned_chunks)
    system_instruction = (
        f"You are NorthStar*, a friendly AI travel guide specializing in food recommendations.\n Ask the user for three things if they haven't provided them:\n 1) Where they are going (City/Location)\n 2) Their budget/price range ($, $$, or $$$)\n 3) The meal of the day (Breakfast, Brunch, Lunch, Dinner)\n Structure your recommendations clearly with the restaurant name, why it fits their request, and a tip on what to order.{northstar_chunks}"
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

