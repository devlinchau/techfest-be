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
from .models import Details

# Create your views here.

load_dotenv()

client = OpenAI(
  api_key=os.getenv('OPENAI_API_KEY'),
)

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
      # return redirect ('chatbot')
      return JsonResponse({'response': 'Account created successfully!'})
    except:
      return JsonResponse({'response': 'Something went wrong! Try again later.'})
  else:
    return JsonResponse({'response': 'Passwords do not match'})

@api_view(['POST', 'GET'])
def details(request):
  # Check if the request method is POST
  if request.method == 'POST':
    income = request.data['income']
    grade = request.data['grade']
    employee_length = request.data['employee_length']
    home_ownership = request.data['home_ownership']

    # Assuming you have a way to associate the details with the current user
    # For example, you can use the authenticated user associated with the request
    if request.user.is_authenticated:
      try:
        details = Details.objects.create(
          user=request.user,
          income=income,
          grade=grade,
          employee_length=employee_length,
          home_ownership=home_ownership
        )
        details.save()
        return JsonResponse({'response': 'Details saved successfully!'})
      except:
        return JsonResponse({'response': 'Error saving details'})
    else:
      return JsonResponse({'response': 'User not authenticated'})

  # Check if the request method is GET
  elif request.method == 'GET':
    # Assuming you want to retrieve details only for the current user
    if request.user.is_authenticated:
      user_details = Details.objects.filter(user=request.user)
      return JsonResponse({'details': user_details.values()})  # Adjust as needed
    else:
      return JsonResponse({'response': 'User not authenticated'})

  # Handle other HTTP methods
  else:
    return JsonResponse({'response': 'Method not allowed'})


# def login(request):
#   return render(request, 'chatbot/login.html')

# def logout(request):
#   return render(request, 'chatbot/logout.html')

def ask_openai(message):
  try:
    response = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": "You are a loan advisor that takes in user input such as annual income and loan ammount and \
         determines if the user's loan request is likely to be approved or rejected. You can also answer general questions about loans."},
        {"role": "user", "content": message}
      ],
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



