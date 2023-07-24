from langchain.llms import OpenAI, AzureOpenAI
import langchain
import openai
from langchain import PromptTemplate, OpenAI, LLMChain
import os
from langchain.chat_models import ChatOpenAI

from langchain.document_loaders import PyPDFLoader

import os  
import PyPDF2  
import docx2txt  
import textract  
# from langchain.document_loader import load_document  
# from langchain import LanguageModel  
  
def load_pdf(document_path):  
    """  
    Load a PDF document and extract the text.  
    """  
    with open(document_path, "rb") as f:  
        # Create a PDF reader object  
        reader = PyPDF2.PdfFileReader(f)  
  
        # Get the number of pages in the PDF  
        num_pages = reader.getNumPages()  
  
        # Initialize the variable to store the text  
        text = ""  
  
        # Loop through each page and extract the text  
        for i in range(num_pages):  
            page = reader.getPage(i)  
            text += page.extractText()  
  
    return text  
  
def load_word(document_path):  
    """  
    Load a Word document and extract the text.  
    """  
    text = docx2txt.process(document_path)  
    return text  
  
def load_text(document_path):  
    """  
    Load a text or HTML document and extract the text.  
    """  
    with open(document_path, "rb") as f:  
        text = f.read().decode("utf-8")  
    return text  
  
def load_other(document_path):  
    """  
    Load a document using the langchain document loader.  
    """  
    doc = PyPDFLoader(document_path)  
    pages = doc.load_and_split()
    print(len(pages))
    return pages  
  
def generate_answer(document_path, question):  
    """  
    Load the document, create a language model, and generate an answer to the question.  
    """  
    # Load the document based on its file extension  
    if document_path.endswith(".pdf"):  
        text = load_other(document_path)  
    elif document_path.endswith(".docx"):  
        text = load_word(document_path)  
    elif document_path.endswith(".txt") or document_path.endswith(".html") or document_path.endswith(".htm"):  
        text = load_text(document_path)  
    elif document_path.endswith(".doc"):  
        text = load_other(document_path)  
    else:  
        raise ValueError("Unsupported document format")  
    
    print(text)
    # Create a language model from the document text  
    # model = LanguageModel(text)  
  
    # Generate an answer to the question using the language model  
    # answer = model.answer(question)  
  
    return text  
  
# Example usage  
document_path = "ticket_booking.pdf"  
question = "What is the main topic of the document?"  
text = generate_answer(document_path, question)  
# print(answer)  
from langchain.vectorstores import FAISS



# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_TYPE"] = "azure"

# openai.api_type = "azure"
# openai.api_key = "baf0d16cb61b40108742e8ece44c72fc"
# openai.api_base = "https://msoaopenai.intel.com"
# openai.api_version = "2023-05-15"
  
# llm = ChatOpenAI(engine = "gpt-4",openai_api_key= "baf0d16cb61b40108742e8ece44c72fc",model_name="gpt-4", openai_api_base="https://msoaopenai.intel.com")

# prompt_template = "explain {model}"

# llm_chain = LLMChain(
#     llm=llm,
#     prompt=PromptTemplate.from_template(prompt_template)
# )

# print(llm_chain.run("intel"))