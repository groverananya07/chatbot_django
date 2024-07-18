import requests
from datetime import datetime
import base64
from openai import OpenAI
from gtts import gTTS
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from bs4 import BeautifulSoup
import json

class ChatBot:
    def __init__(self, profession):
        self.chat_history = []
        self.gpt_client = OpenAI(api_key="sk-proj-h2ACTULQJBaXBC9K16gXT3BlbkFJVAHzm0cl1pUahrAz98Zi")
        self.weather_api_key = "8822a20b5e898df26d1a5686f0108308"
        self.google_api_key = "AIzaSyAm5WNX-Msjwp83ornSgrhDTmXobx5k4aw"
        self.cse_id = '635db50b84a44417d'
        self.profession = profession

        self.system_content = f"A profession {profession} is assigned to you. Generate a name for that given profession, tell the user your specialty and greetings. Also, give client responses based on that profession only. If the user asks questions regarding any other profession, kindly deny them."

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

    def process_message(self, user_content, temperature=0.7, model="gpt-4o-2024-05-13"):
        response = self.gpt_client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the message given by the user and check explicitly the requirement for searching online, if the user message includes question regarding current data or information search online,return it in json format and check if {'system_online':<true/false> ,'search_weather':<true/false>}"
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=temperature,
        )
        return json.loads(response.choices[0].message.content)

    def ask(self, message):
        self.chat_history.append({'message': message, 'role': self.profession})
        gpt_response = self.process_message(message)
        print("Process message response:", gpt_response)
        
        system_online = gpt_response.get('system_online', False)
        search_weather = gpt_response.get('search_weather', False)
        
        if search_weather:
            city = "Delhi"  # Replace with actual logic to extract city
            weather_response = self.get_weather(city)
            return weather_response
        elif system_online:
            print("Searching online")
            google_response = self.google_search(message)
            return google_response
        else:
            gpt_response = self.gpt_bot(message)
        
        self.chat_history.append({'message': gpt_response, 'role': "Jarvis"})
        return gpt_response

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

    def google_search(self, query):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'key': self.google_api_key,
            'cx': self.cse_id,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.HTTPError as http_err:
            return f"HTTP error occurred: {http_err}"
        except requests.exceptions.RequestException as err:
            return f"Other error occurred: {err}"

        search_results = response.json().get('items', [])
        if not search_results:
            return "No search results found."

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for result in search_results:
            first_result_url = result['link']
            print(f"Trying URL: {first_result_url}")

            try:
                page_response = requests.get(first_result_url, headers=headers)
                page_response.raise_for_status()
                
                soup = BeautifulSoup(page_response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                headings = soup.find_all(['h2', 'h3', 'h4'])

                page_text = "\n\n".join([heading.get_text() for heading in headings[:5]]) + "\n\n" + "\n\n".join([para.get_text() for para in paragraphs[:10]])

                if page_text:
                    return page_text
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred while fetching webpage: {http_err}")
            except requests.exceptions.RequestException as err:
                print(f"Other error occurred while fetching webpage: {err}")

        return "All attempts to fetch the webpage content failed."

    def generate_voice_message(self, text, filename="output.mp3"):
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        print(f"Voice message saved as {filename}")

    def record_audio(self, duration=5, filename="recording.wav", sample_rate=44100):
        print("Recording...")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype='int16')
        sd.wait()  # Wait until recording is finished
        write(filename, sample_rate, recording)
        print(f"Recording saved as {filename}")
