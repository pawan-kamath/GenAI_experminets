import openai  
import PyPDF2  
  
# Set up the OpenAI API key  
openai.api_type = "azure"
openai.api_key = "baf0d16cb61b40108742e8ece44c72fc"
openai.api_base = "https://msoaopenai.intel.com"
openai.api_version = "2023-05-15" 
  
# Load the PDF file  
with open('ticket_booking.pdf', 'rb') as f:  
    # Create a PDF reader object  
    reader = PyPDF2.PdfReader(f)  
  
    # Get the number of pages in the PDF  
    num_pages = reader.pages 
  
    # Initialize the variable to store the text  
    text = ""  
  
    # Loop through each page and extract the text  
    for i in range(len(num_pages)):  
        page = reader.pages[i]
        text += page.extract_text()

print(text)
# Set up the OpenAI model  
model_engine = "GPT35Turbo"   # Or any other model engine  
prompt = f"What is the main topic of the PDF?\n\n{text}"  
temperature = 0.7   # Adjust as needed  
max_tokens = 60     # Adjust as needed  
stop_sequence = "\n\n"   # Stop the prompt at the end of the first paragraph  
  
# Generate the answer using the OpenAI model  
response = openai.Completion.create(  
    engine=model_engine,  
    prompt=prompt,  
    temperature=temperature,  
    max_tokens=max_tokens,  
    stop=stop_sequence  
)  

print(response)
# Print the answer  
answer = response.choices[0].text.strip()  
print(answer)  
