import requests
from datetime import datetime
import base64
from openai import OpenAI


class ChatBot:
    def __init__(self, profession):
        self.chat_history = []
        self.gpt_client = OpenAI(api_key="")
        self.weather_api_key = ""
        self.profession = profession
        self.google_api_key = ""
        self.cse_id = ''
        
        self.system_content = ""
        response = self.gpt_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Answer the user query directly, Do not write extra sentences and write in 2nd person tone",
                },
                {
                    "role": "user",
                    "content": f"You are given a professional {profession}. You have to generate a name a person for this profession, generate how it should behave and how it should respond to the client generally"
                }
            ],
            temperature=0.3,
        )
        print(response.choices[0].message.content)
        self.system_content = response.choices[0].message.content
        # print(self.system_content)

    def gpt_bot(self, message, model="gpt-4o-2024-05-13", temperature=0.7):
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        user_content = message + f"\n\n\nCurrent information: {current_datetime_str}\n\n\nChat history: {self.chat_history}"

        response = self.gpt_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": self.system_content
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    
    

    def ask(self, message):
        self.chat_history.append({'message': message, 'role': self.profession})
        gpt_response = self.gpt_bot(message)
        self.chat_history.append({'message': gpt_response, 'role': "Jarvis"})
        return gpt_response
    
    
    def search_google(self, message):

        pass

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def read_image(self, message, image_path):
        base64_image = self.encode_image(image_path)
        response = self.gpt_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ],
                }
            ],
            max_tokens=300,
        )
        return response.choices[0].message['content']

    def get_weather(self, city):
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
        response = requests.get(weather_url)
        if response.status_code == 200:
            weather_data = response.json()
            weather_description = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            return f"The weather in {city} is currently {weather_description} with a temperature of {temperature}°C."
        else:
            return "I'm sorry, I couldn't retrieve the weather information for that location."
        

    def generate_user_image(self, user_details):
        # Example implementation: user_details should be a dictionary containing details to describe the image
        message = f"Generate an image of a person based on the following details: {user_details}"
        # Provide a path to an image file you want to use as context for generating the image
        image_path = "path/to/your/image.jpg"
        
        # Use the generate_image_response method to interact with DALL-E and generate the image
        image_response = self.generate_image_response(message, image_path)
        
        return image_response
    
    def google_search(self, query):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': self.google_api_key,
            'cx': self.cse_id,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            search_results = response.json().get('items', [])
            result_texts = []
            for result in search_results:
                result_texts.append(result['snippet'])
            return "\n\n".join(result_texts)
        else:
            return "Error fetching search results."