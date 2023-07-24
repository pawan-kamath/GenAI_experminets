import json
import math
import os
import time

import openai
import openai.error
import pandas as pd
import tiktoken
from openai import embeddings_utils
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import requests
from bs4 import BeautifulSoup

enc = tiktoken.encoding_for_model("gpt-4")
openai.api_type = "azure"
openai.api_key = "baf0d16cb61b40108742e8ece44c72fc"
openai.api_base = "https://msoaopenai.intel.com"
openai.api_version = "2023-05-15"
  
def setup():
    nltk.download('punkt')
    nltk.download('stopwords')

def clean_text(text: str) -> str:
    translation_table = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text = text.translate(translation_table)

    words = word_tokenize(text)

    filler_words = set(stopwords.words('english'))
    words = [word for word in words if word.lower() not in filler_words]

    text = ' '.join(words)
    return text

def get_text_embeds(text: str) -> tuple[str, list[float], int]:
    # cleaned = clean_text(text)
    cleaned = text.strip().replace("\n", "")

    response = openai.Embedding.create(
        input=cleaned,
        engine="text-embedding-ada-002"
    )

    try:
        embeddings = response['data'][0]['embedding']
        total_tokens = int(response['usage']['total_tokens'])
    except:
        print(f"Could not get embeddings for {text}")
        embeddings = []
        total_tokens = 0
    
    return cleaned, embeddings, total_tokens

def read_webpage(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the text from the parsed HTML
        text = soup.get_text()
        
        return text
    else:
        print("Error: Unable to retrieve the webpage.")
        return None

def chunk_text(input_text):
    max_length = 8191
    overlap_size = 200 # Not to loose context
  
    # Split the input text into overlapping chunks  
    chunks = []  
    start = 0  
    while start < len(input_text):  
        end = start + max_length  
        if end >= len(input_text):  
            end = len(input_text)  
        else:  
            end -= overlap_size  
            if end > start:  
                end = input_text.rfind(" ", start, end) + 1  
        chunk = input_text[start:end]  
        chunks.append(chunk)  
        start = end
        print(chunk)

    print(len(chunks))  
    return chunks

def ask_gpt(role, prompt):
    attempts = 0
    while attempts < 5:
        try:
            response = openai.ChatCompletion.create(
                engine="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": role,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=900,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
            )

            return response
        except openai.error.RateLimitError as e:
            # If a RateLimitError occurs, wait for 5 seconds and try again
            attempts += 1
            print(f"Connection {attempts} failed, waiting for 5 seconds...")
            time.sleep(5)


def get_summary(content):
    role = "You are an AI assistant that is highly detail oriented. You take excellent meeting notes."
    prompt = f"summarize the following: {content}"

    response = ask_gpt(role, prompt)

    total_tokens = response["usage"]["total_tokens"]  # type: ignore
    print(f"tokens used: {total_tokens}")
    summary = response["choices"][0]["message"]["content"]  # type: ignore
    return summary

# Define a function to read Markdown files and convert them to plain text  
def read_markdown_files(directory):  
    text = ""  
    for filename in os.listdir(directory):  
        if filename.endswith(".md"):  
            with open(os.path.join(directory, filename), encoding="utf-8") as f:  
                text += f.read() + "\n\n"  
    return text

def send_question_request_with_context(question: str, context: list[str], attempt: int=0):
    context_joined = '\n'.join(context)
    prompt = f"You are an Engineering Assistant that provides domain knowledge to a question, using only the following historical context to aid your answer: {context_joined}"

    try:
        response = openai.ChatCompletion.create(
            engine="gpt-4",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": question}],
        )
    except openai.error.RateLimitError:
        if attempt < 3:
            print("Rate Limited, trying again")
            time.sleep(2*(attempt + 1))
            
            response = send_question_request_with_context(question=question, context=context, attempt=attempt+1)
        else:
            raise

    return response

def get_relevant_context_using_embeds(question_embed: list[float], embed_df: pd.DataFrame) -> list[str]:
    similarities = [
        (idx, embeddings_utils.cosine_similarity(question_embed, vector))
            for idx, vector in enumerate(embed_df["post_embed"])]

    similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

    similar_indices = [sim[0] for sim in similarities[:5]]
    
    return embed_df.iloc[similar_indices].post_tokens.to_list()


def ask_question(question: str, embed_df: pd.DataFrame) -> tuple[str, int]:
    cleaned, question_embed, embed_tokens = get_text_embeds(text=question)
    print("Question Embedded")
    
    context = get_relevant_context_using_embeds(question_embed=question_embed, embed_df=embed_df)
    print_ctx = '\n'.join([f"{idx}: {ctx}" for idx, ctx in enumerate(context)])
    print(f"Found context: {print_ctx}")

    response = send_question_request_with_context(question=question, context=context)

    try:
        chat_response = response["choices"][0]["message"]["content"]
        tokens_used = response["usage"]["total_tokens"]
    except Exception as ex:
        print(f"Could not get an answer to the question {question} due to an exception: {ex}")
        chat_response = "Error in Response"
        tokens_used = 0

    tokens_used = int(tokens_used) + embed_tokens

    return chat_response, tokens_used

def main():
    setup()
    # wiki_page = "https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/wiki"
    wiki_page ="https://en.wikipedia.org/wiki/ChatGPT"
    # Call the function to read the webpage contents
    # wiki_text = read_webpage(wiki_page)

    wiki_text = read_markdown_files("../applications.manufacturing.intel.fab-data-analytics.iris2.wiki")
    # Print the contents to the console
    cleaned_text = clean_text(wiki_text)
    print("Embedding the texts")
    chunks = chunk_text(cleaned_text)
    df = pd.DataFrame()
    embeddings_chunks = []
    for chunk in chunks:
        cleaned, embeddings, total_tokens = get_text_embeds(chunk)
        print(total_tokens)
        embeddings_chunks.append(embeddings)
    
        print(type(embeddings))
    df["chunk"] = chunks
    df["embedding"] = embeddings_chunks
    df.to_csv("embedding_wiki.csv",index=False)

    summary = get_summary(chunks[1])       
    print(summary)


main()
