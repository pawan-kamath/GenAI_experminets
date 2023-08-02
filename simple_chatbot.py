import os
import openai
from langchain.document_loaders import UnstructuredMarkdownLoader,UnstructuredFileLoader,TextLoader,PyPDFLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI, AzureOpenAI
import langchain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
from pdf2embed_langchain import (clean_text,
                                 preprocess_document,
                                 pdf_loader,
                                 chunking,
                                 embedding_store
                                 )
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.agents import Tool
from langchain.agents import initialize_agent
from langchain.vectorstores.pgvector import PGVector
from langchain.vectorstores import PGEmbedding

def chatbot(llm,vector_store):
    conversational_mem = ConversationBufferMemory(memory_key="chat_history",k=10,return_messages=True)#, input_key='input', output_key="output")
    qa = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type="stuff",
        retriever = vector_store.as_retriever(),
    )

    tools = [
        Tool(
            name="UKP",
            func = qa.run,
            description=(
                'use this tool for any document ingestion to having a QA session'
            )
        )
    ]

    agent = initialize_agent(
        agent = 'chat-conversational-react-description',
        tools = tools,
        llm=llm,
        verbose=False,
        max_iterations = 3,
        early_stopping_method = 'generate',
        memory=conversational_mem,
        # return_source_documents = True,
        # return_intermediate_steps=True
    )
    while True:
        query = input("What do you want to discuss about?\n")
        if query.lower() == "exit":
            break
        response = agent(query)
        print(response["output"])


def talk2doc(llm,vector_store):
    qa = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type="stuff",
        retriever = vector_store.as_retriever(),
        return_source_documents = True
    )
    
    while(True):
        query = input("How may i help you?\n")
        if query.lower() == "exit":
            break
        response = qa({"query":query})
        print(f"AI Response: {response['result']}")
        print(f"source: {response['source_documents'][0]}")

def main():
    print("\n\nHello! Welcome to UKP.\nHow may I help you today?")
    print("\nPlease provide the path to your document")
    file_path = input()
    print("\nThank you, processing your document...")
    doc_pdf = pdf_loader(file_path)
    chunked_docs = chunking(doc_pdf)
    conn,model = embedding_store("quivr",chunked_docs)
    llm = AzureChatOpenAI(deployment_name = "GPT35Turbo",openai_api_key= "baf0d16cb61b40108742e8ece44c72fc",model_name="GPT35Turbo", openai_api_base="https://msoaopenai.intel.com",openai_api_version="2023-05-15", openai_api_type="azure")
    
    COLLECTION_NAME = "quivr"

    vector_store = PGVector(
        embedding_function=model,
        collection_name=COLLECTION_NAME,
        connection_string="postgresql://postgres:1234567890@10.114.237.142:5433/quivr"
    )
    
    print("Ok! It's a interesting document.\nWould you like to 1. ask me question on the document or 2. you want to discuss with me on this document?")
    option = input("Choose 1 or 2\n")
    if int(option) == 1:
        talk2doc(llm,vector_store)
    elif int(option) == 2:
        chatbot(llm,vector_store)
    else:
        print("invalid option")

if __name__ == "__main__":
    main()