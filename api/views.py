from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dotenv import load_dotenv
import os
from openai import OpenAI
import openai
from django.contrib import messages, auth
from django.contrib.auth.models import User

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
  return JsonResponse({'response': response})

def login(request):
  return render(request, 'chatbot/login.html')

@api_view(['POST'])
def register(request):
  username = request.data['username']
  email = request.data['email']
  password1 = request.data['password1']
  password2 = request.data['password2']
  if password1 == password2:
    try:
      user = User.objects.create_user(username=username, email=email, password=password1)
      user.save()
      auth.login(request, user)
      return redirect('chatbot')
    except:
      return JsonResponse({'response': 'Something went wrong! Try again later.'})
  else:
    return JsonResponse({'response': 'Passwords do not match'})

def logout(request):
  return render(request, 'chatbot/logout.html')

