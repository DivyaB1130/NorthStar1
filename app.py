import gradio as gr
from huggingface_hub import InferenceClient

# This is the same pattern from the Generative AI lesson! It uses the
# Inference Provider API to send your messages to an AI model and get
# a response back. Swap out the model below for a different one if
# you want to experiment!
#
# Note: if this Space doesn't already have one, you'll need to add an
# HF_TOKEN secret in the Space's Settings tab for this to work
# (Settings -> Variables and secrets -> New secret).

client = InferenceClient("Qwen/Qwen2.5-7B-Instruct", bill_to="kode-with-klossy")

import kagglehub #importing static yelp dataset to test accuracy
path = kagglehub.dataset_download("yelp-dataset/yelp-dataset")
print("Path to dataset files:", path)

def preprocess_text(text):
  # Strip extra whitespace from the beginning and the end of the text
  cleaned_text = text.strip()
  # Split the cleaned_text by every newline character (\n)
  chunks = cleaned_text.split("\n")
  # Create an empty list to store cleaned chunks
  cleaned_chunks = []
  # Write your for-in loop below to clean each chunk and add it to the cleaned_chunks list
  for chunk in chunks:
    if chunk != ():
      cleaned_chunks.append(chunk)
  # Print cleaned_chunks
  print(cleaned_chunks)
  # Print the length of cleaned_chunks
  print(len(cleaned_chunks))
  # Return the cleaned_chunks
  return cleaned_chunks

# Call the preprocess_text function and store the result in a cleaned_chunks variable
cleaned_chunks = preprocess_text(path)
def testing():
    print(path.head())


def respond(message, history):
    messages = [{"role": "system", "content": "You are a friendly chatbot."}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": message})

    response = client.chat_completion(
        messages,
        max_tokens=100, temperature=1.3
    )

    return response.choices[0].message.content.strip()

chatbot = gr.ChatInterface(respond, testing)

chatbot.launch()


# TODO: This is just a starting point! Customize the system prompt,
# the model, and the interface to make this project your own!
