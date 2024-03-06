from langchain.embeddings import OpenAIEmbeddings 
from langchain.document_loaders import UnstructuredURLLoader 
from langchain.vectorstores import DocArrayInMemorySearch 
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain.chat_models import ChatOpenAI 
from langchain.llms import OpenAI 
from langchain.chains import ConversationalRetrievalChain 
from langchain.prompts.prompt import PromptTemplate 
from langchain.memory import ConversationBufferMemory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
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
    # print("Result: ", result["choices"][0]["message"]["function_call"]["name"])
    function_name = result["choices"][0]["message"]["function_call"]["name"]
    func = globals()[function_name]
    return func(user_message)

# should be called by openai function calling
# providing the prompt and the database scheme, it should return the sql query
def get_sql_query(prompt):
    sql_scheme = """
    class Inventory(Base):
        __tablename__ = 'inventory'

        id = Column(Integer, primary_key=True)
        sku = Column(String)
        product_name = Column(String)
        quantity = Column(Integer)
        price = Column(Float)
        size = Column(String)
        color = Column(String)
        brand = Column(String)
        image = Column(String)
        description = Column(String)
    """
    final_prompt = """
        This is what user is asking for: {prompt}, this is the sql scheme in the database: {sql_scheme}.
        Now based on the provided information, please give me a valid JSON response with the key "query", 
        the value should be a raw SQL query to get what user is asking for. Avoid any extra information in the response.
        Output format is JSON only, no markdown permitted (no ```).
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
    data = json.loads(result['choices'][0]['message']['content'])
    sql_query = data['query']

    try:
        # Connect to the database
        engine = create_engine('postgresql://doruk:doruk@localhost:5432/available_inventory')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Execute the SQL query
        result = session.execute(text(sql_query))
        # print("Result from db access: ", result)
        
        data_values = result.mappings().all()

        print("Result from db access: ", data_values)
        
        return data_values
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None
    finally:
        # Close the session
        session.close()
        
    
def regular_response(user_message):
    print("I am an AI model, I am still learning. I cannot understand your message.")
    return "I am an AI model, I am still learning. I cannot understand your message."


if __name__ == "__main__":
    generate_ai_response("Hi, can you show me all the products in color 'Red'?.")
