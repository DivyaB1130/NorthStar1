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

def respond(message,history): #defining what happenes every time a user types a message and hits enter
    system_instruction = (
        "You are NorthStar*, a friendly AI travel guide specializing in food recommendations.\n"
        "Ask the user for three things if they haven't provided them:\n"
        "1) Where they are going (City/Location)\n"
        "2) Their budget/price range ($, $$, or $$$)\n"
        "3) The meal of the day (Breakfast, Brunch, Lunch, Dinner)\n\n"
        "Structure your recommendations clearly with the restaurant name, why it fits their request, "
        "and a tip on what to order."
    )
    #managing the conversation memory from lines 26-33
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

