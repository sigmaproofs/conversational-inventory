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
import json
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

def generate_ai_response(user_message):
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {
            "role": "user",
            "content": user_message
            }
        ],
        "functions": [
            {
                "name": "get_sql_query",
                "description": "query database for the user's requested items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_message": {
                            "type": "string",
                            "description": "The message of user, explaining what they are looking for."
                        },
                    }
                }
            },
            {
                "name": "regular_response",
                "description": "response to user's message, used when there is no need to query the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_message": {
                            "type": "string",
                            "description": "The message of user."
                        },
                    }
                }
            }
        ]
    }
    headers = {"Authorization": f"Bearer {openai_api_key}"}

    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    function_name = result["choices"][0]["message"]["function_call"]["name"]
    func = globals()[function_name]
    return func(user_message)

# should be called by openai function calling
# providing the prompt and the database scheme, it should return the sql query
def get_sql_query(prompt):
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
    print("Prompt: ", prompt)
    # print("SQL Scheme: ", sql_scheme)
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
    print("Result: ", result['choices'][0]['message']['content'])
    return result['choices'][0]['message']['content']
    
    
def regular_response(user_message):
    print("I am an AI model, I am still learning. I cannot understand your message.")
    return "I am an AI model, I am still learning. I cannot understand your message."

if __name__ == "__main__":
    generate_ai_response("Hi, I want to see all the product prices in the inventory.")
