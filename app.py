import telebot
from telebot import types
from langchain.embeddings import OpenAIEmbeddings 
from langchain.document_loaders import UnstructuredURLLoader 
from langchain.vectorstores import DocArrayInMemorySearch 
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain.chat_models import ChatOpenAI 
from langchain.llms import OpenAI 
from langchain.chains import ConversationalRetrievalChain 
from langchain.prompts.prompt import PromptTemplate 
from langchain.memory import ConversationBufferMemory
import requests
from enum import Enum, auto
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create a TeleBot instance using the API token 
bot = telebot.TeleBot(BOT_TOKEN)

openai_api_key = os.getenv("OPENAI_API_KEY")



# loader = UnstructuredURLLoader(urls=urls)
# docs = loader.load()

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 
# docs = text_splitter.split_documents(docs)

# embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

# project for Raylu AI Application, based on job posting example.

custom_template = """You are a sales agent for a specific store, your job is to help user to make purchase. 
    Keep the answer as concise as possible. Avoid making up answers and if you don't have information, simply say it and apologize.
    Always be polite and helpful.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

CUSTOM_QUESTION_PROMPT = PromptTemplate.from_template(custom_template)

model = ChatOpenAI(model_name="gpt-4", temperature=0.0, openai_api_key=openai_api_key) 
# vectordb = DocArrayInMemorySearch.from_documents(docs, embeddings) 
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True) 
qa = ConversationalRetrievalChain.from_llm(
    model,
    # vectordb.as_retriever(),
    condense_question_prompt=CUSTOM_QUESTION_PROMPT,
    memory=memory
)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Hello! I'm your AI shopping assistant. Tell me what are you looking for today?")
    bot.send_message(message.chat.id, "Example message is, Do you have any purple t-shirt? If yes, please list them for me.")
    

# Define a message handler for regular text messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Extract the user's message
    user_message = message.text

    # Use your AI model to generate a response
    response = generate_ai_response(user_message)
    

    # Send the response back to the user
    bot.send_message(message.chat.id, response)

def generate_ai_response(user_message):
    sql_scheme = """
    class StockInventory(Base):
        __tablename__ = 'stock_inventory'

        id = Column(Integer, primary_key=True)
        product_name = Column(String)
        quantity = Column(Integer)
        price = Column(Float)
        last_updated = Column(DateTime)
        size = Column(String)
        color = Column(String)
        brand = Column(String)
        image = Column(String)
    """
    response = get_sql_query(user_message, sql_scheme)
    return response
    # response = qa({"question": user_message})  

    # return response['answer']

# should be called by openai function calling
# providing the prompt and the database scheme, it should return the sql query
def get_sql_query(prompt, sql_scheme):
    final_prompt = """
        This is what user is asking for: {prompt}, this is the sql scheme in the database: {sql_scheme}.
        Now based on the provided information, please give me a JSON response with the key "query", 
        the value should be a raw SQL query to get what user is asking for. Avoid any extra information in the response.
    """
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {"role": "system", "content": "You are an SQL expert."},
            {"role": "user", "content": final_prompt.format(prompt=prompt, sql_scheme=sql_scheme)}
        ]
    }
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    return result['choices'][0]['message']['content']
    
    

if __name__ == "__main__":
    bot.polling()