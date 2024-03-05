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

urls=[
    'https://www.otolawn.com/',
    'https://otolawn.com/pages/why-oto',
    'https://otolawn.com/pages/step-2',
    'https://otolawn.com/pages/warranty',
    'https://otolawn.com/pages/contact-us',
]

loader = UnstructuredURLLoader(urls=urls)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 
docs = text_splitter.split_documents(docs)

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

custom_template = """Use the following pieces of context to answer the question as if you are a lawn care assistant. 
    Keep the answer as concise as possible. Avoid making up answers and if you don't have information, simply say it and apologize.
    Always be polite and helpful. Try to give as much information as possible.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

CUSTOM_QUESTION_PROMPT = PromptTemplate.from_template(custom_template)

model = ChatOpenAI(model_name="gpt-4", temperature=0.0, openai_api_key=openai_api_key) 
vectordb = DocArrayInMemorySearch.from_documents(docs, embeddings) 
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True) 
qa = ConversationalRetrievalChain.from_llm(
    model,
    vectordb.as_retriever(),
    condense_question_prompt=CUSTOM_QUESTION_PROMPT,
    memory=memory
)

# Define user state enumeration
class UserState(Enum):
    AWAITING_CHOICE = auto()
    AWAITING_AICHAT = auto()
    AWAITING_IMAGE_FOR_DIAGNOSIS = auto()
    AWAITING_LOCATION = auto()
    AWAITING_WATER_SCHEDULE = auto()
    AWAITING_SUNLIGHT_EXPOSURE = auto()
    AWAITING_IMAGE_FOR_IDENTIFICATION = auto()
    AWAITING_SOLUTIONS_RECOMMENDATION = auto()

# Initialize user states
user_states = {}
user_info = {}

# Define the watering schedule options and sunlight exposure options.
watering_schedule_options = ["Every day", "Every 2 days", "2 times a week", "Every week", "Every 2 weeks", "Less often than every 2 weeks"]
sunlight_exposure_options = ["Indirect sunlight", "Full shade", "Partial sun", "Full sun"]

# Define a command handler for the /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Identify plants', 'Diagnose diseases', 'Chat about my lawn')
    bot.send_message(chat_id, "Hello! I'm HeyOtO, your lawn care AI assistant. What do you want to do today?", reply_markup=markup)
    user_states[chat_id] = UserState.AWAITING_CHOICE

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_CHOICE)
def handle_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == 'Diagnose diseases':
        bot.send_message(chat_id, "Please send a clear image of the plant.")
        user_states[chat_id] = UserState.AWAITING_IMAGE_FOR_DIAGNOSIS
    elif choice == 'Identify plants':
        bot.send_message(chat_id, "Please send me a picture of the plant you want to identify.")
        user_states[chat_id] = UserState.AWAITING_IMAGE_FOR_IDENTIFICATION
    else:
        bot.send_message(chat_id, "How can I help you? I can answer your lawn related questions or any question about your OtO device.")
        user_states[chat_id] = UserState.AWAITING_AICHAT

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_AICHAT)
def handle_message(message):
    history = memory.load_memory_variables({}) # add chat history
    # Handle chat about my lawn or other choices if needed
    user_message = message.text
    # Use AI model to generate a response
    response = generate_ai_response(user_message)

    bot.send_message(message.chat.id, response)

def generate_ai_response(user_message):
    # Query AI model with the user's message
    # response = qa_stuff.run(user_message)

    # print('user_msg', user_message)

    response = qa({"question": user_message})  

    return response['answer']

def present_main_options(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Identify plants', 'Diagnose diseases', 'Chat about my lawn')
    bot.send_message(chat_id, "Do you have any other questions? What do you want to do next?", reply_markup=markup)
    user_states[chat_id] = UserState.AWAITING_CHOICE

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_LOCATION)
def handle_location(message):
    chat_id = message.chat.id
    user_info[chat_id]['location'] = message.text
    user_states[chat_id] = UserState.AWAITING_WATER_SCHEDULE
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for option in watering_schedule_options:
        markup.add(types.KeyboardButton(option))
    bot.send_message(chat_id, "How often do you water the plant?", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_WATER_SCHEDULE)
def handle_water_schedule(message):
    chat_id = message.chat.id
    user_info[chat_id]['water'] = watering_schedule_options.index(message.text)  # Store the index of the selected option
    user_states[chat_id] = UserState.AWAITING_SUNLIGHT_EXPOSURE
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for option in sunlight_exposure_options:
        markup.add(types.KeyboardButton(option))
    bot.send_message(chat_id, "How much sunlight does the plant get?", reply_markup=markup)

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_IMAGE_FOR_DIAGNOSIS)
def handle_diagnosis_image(message):
    chat_id = message.chat.id
    user_states[chat_id] = UserState.AWAITING_LOCATION
    user_info[chat_id] = {'image_id': message.photo[-1].file_id}
    bot.send_message(chat_id, "Got the image! Now, please enter your location.")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_SUNLIGHT_EXPOSURE)
def handle_sunlight_exposure(message):
    chat_id = message.chat.id
    user_info[chat_id]['sunlight'] = sunlight_exposure_options.index(message.text)  # Store the index of the selected option
    bot.send_message(chat_id, "Diagnosing your plant...")
    call_diagnose_api(chat_id)

def call_diagnose_api(chat_id):
    location = user_info[chat_id]['location']
    water = user_info[chat_id]['water']
    sunlight = user_info[chat_id]['sunlight']
    image_id = user_info[chat_id]['image_id']
    
    # Retrieve the image file using the file_id
    file_info = bot.get_file(image_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = BytesIO(downloaded_file)
    image_stream.name = 'plant_disease.jpg'

    files = {'file': image_stream}
    data = {
        'location': location,
        'water': water,
        'sunlight': sunlight
    }

    # Send the POST request to the API
    response = requests.post("https://heyoto-service-ugegz6xfpa-uc.a.run.app/health", data=data, files=files)

    if response.status_code == 200:
        # Process the successful response
        diagnosis_result = response.json()
        # Send the diagnosis result to the user
        user_info[chat_id]['diagnosis_result'] = diagnosis_result
        final_decision_list = diagnosis_result.get("final decision", [])
        final_decision_str = "\n".join(final_decision_list)
        bot.send_message(chat_id, f"The diagnosis is:\n{final_decision_str}")

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Recommend Solutions')
        bot.send_message(chat_id, "Would you like to get recommendations for solutions?", reply_markup=markup)
        user_states[chat_id] = UserState.AWAITING_SOLUTIONS_RECOMMENDATION
    else:
        # Handle the failed response
        bot.send_message(chat_id, "Failed to diagnose the plant. Please try again later.")

    # Reset user state or set it to the next expected action
    # memory.save_context({"input": ""}, {"output": diagnosis_result})
    image_stream.close()

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_SOLUTIONS_RECOMMENDATION)
def handle_solutions_recommendation(message):
    chat_id = message.chat.file_id
    if message.text == 'Recommend Solutions':
        # Call the solutions API with the stored diagnosis result
        diagnosis_result = user_info[chat_id].get('diagnosis_result')
        data = {
            'disease': diagnosis_result[0]
        }
        # if diagnosis_result:
        response = requests.post("https://heyoto-service-ugegz6xfpa-uc.a.run.app/solution", data=data)
        print(response)
        if response.status_code == 200:
            solutions_result = response.json()
            # Send the solutions result to the user
            bot.send_message(chat_id, f"The recommended solutions are:\n{solutions_result}")
        else:
            bot.send_message(chat_id, "Failed to get solutions. Please try again later.")
        # memory.save_context({"input": ""}, {"output": diagnosis_result})
        present_main_options(chat_id)


@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.chat.id) == UserState.AWAITING_IMAGE_FOR_IDENTIFICATION)
def handle_identification_image(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Processing your image...")

    # Retrieve file information from the message.photo list
    file_info = bot.get_file(message.photo[-1].file_id)

    # Download the image from the Telegram server
    downloaded_file = bot.download_file(file_info.file_path)

    # Convert the binary data to a bytes-like object for multipart/form-data
    image_stream = BytesIO(downloaded_file)
    image_stream.name = 'plant.jpg'

    files = {'file': image_stream}
    response = requests.post("https://heyoto-service-ugegz6xfpa-uc.a.run.app/identify", files=files)

    if response.status_code == 200:
        # Process the successful response
        result = response.json()
        # Depending on the API response structure, extract and send the result
        bot.send_message(chat_id, 
        (
            f"Plant identified:\n"
            f"Name: {result.get('name', 'N/A')}\n"
            f"Hardiness: {result.get('hardiness', 'N/A')}\n"
            f"Hardiness Zones: {result.get('hardiness_zones', 'N/A')}\n"
            f"Soil: {result.get('soil', 'N/A')}\n"
            f"Sunlight: {result.get('sunlight', 'N/A')}\n"
            f"Difficulty: {result.get('difficulty', 'N/A')}\n"
            f"Planting Time: {result.get('planting_time', 'N/A')}\n"
            f"Fertilization: {result.get('fertilization', 'N/A')}\n"
            f"Pruning: {result.get('pruning', 'N/A')}\n"
            f"Watering: {result.get('watering', 'N/A')}\n"
            f"Plant Type: {result.get('plant_type', 'N/A')}\n"
            f"Animal Resistance: {result.get('animal_resistance', 'N/A')}\n"
            f"Average Size: {result.get('average_size', 'N/A')}\n"
            f"Growth Rate: {result.get('growth_rate', 'N/A')}\n"
            f"Pet Warning: {result.get('pet_warning', 'N/A')}\n"
            f"Common Name: {result.get('common_name', 'N/A')}\n"
            f"Bloom Season: {result.get('bloom_season', 'N/A')}"
        ))
    else:
        bot.send_message(chat_id, "Failed to identify the plant. Please try again later.")

    # memory.save_context({"input": ""}, {"output": result})
    # user_states[chat_id] = UserState.AWAITING_CHOICE
    image_stream.close()

if __name__ == "__main__":
    bot.polling()