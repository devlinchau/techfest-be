from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dotenv import load_dotenv
import os
from openai import OpenAI
import openai
from django.contrib import messages

# Create your views here.

load_dotenv()

client = OpenAI(
  api_key=os.getenv('OPENAI_API_KEY'),
)

def ask_openai(message):
  try:
    response = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message}
      ],
      max_tokens=150,
      temperature=0.6,
    )
    print(response)
    answer = response.choices[0].message.content.strip()
    return answer
  except openai.APIConnectionError as e:
    #Handle connection error here
    messages.warning(f"Failed to connect to OpenAI API, check your internet connection")
  except openai.RateLimitError as e:
    #Handle rate limit error (we recommend using exponential backoff)
    messages.warning(f"You exceeded your current quota, please check your plan and billing details.")
    messages.warning(f"If you are a developper change the API Key")

@api_view(['POST'])
def chatbot(request):
  message = request.data['message']
  response = ask_openai(message)
  return JsonResponse({'message': message, 'response': response})

