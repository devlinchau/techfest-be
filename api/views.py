from django.shortcuts import render, redirect
from django.http import JsonResponse
import pandas as pd
import joblib
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dotenv import load_dotenv
import os
from openai import OpenAI
import openai
from django.contrib import messages, auth
from django.contrib.auth.models import User
from .models import Details
import json
from sklearn.preprocessing import OneHotEncoder

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
      return JsonResponse({'response': 'Account created successfully!', 'username': user.username})
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

  elif request.method == 'GET':
    if request.user.is_authenticated:
      user_details = Details.objects.filter(user=request.user)
      # print(user_details.values())
      # print(user_details.values()[0])
      # print(request.user.username)
      return JsonResponse({'details': user_details.values()[0]}) 
    else:
      return JsonResponse({'response': 'User not authenticated'})
  else:
    return JsonResponse({'response': 'Method not allowed'})

@api_view(['POST'])
def login(request):
  username = request.data['username']
  password = request.data['password']
  user = auth.authenticate(username=username, password=password)
  if user is not None:
    auth.login(request, user)
    return JsonResponse({'response': 'Login successful!'})
  else:
    messages.error(request, 'Invalid credentials')


def logout(request):
  auth.logout(request)
  

def ask_openai(message):
  original_messages = [
        {"role": "system", "content": r"You are a loan advisor that takes in the user input: loan amount (loan_amnt), interest rate (int_rate), \
         annual income (annual_inc), term (either 36 or 60 months), credit score (grade), and purpose (debt_consolidation, small_business, home_improvement,\
        'major_purchase', 'credit_card', 'other', 'house', 'medical',\
        'car', 'vacation', 'moving', 'renewable_energy', 'wedding',\
        'educational'). You are to convert this user input into a JSONResponse with the following format and send it back to the user:\
         {\"loan_amnt\": x, \"int_rate\": x, \"annual_inc\": x, \"term\": \" x\", \"grade\": \"x\", \"purpose\": \"x\", where x are the user's inputs. Make sure to save interest rate as an integer value and include a space before the term value. For example, \" 36 months\" instead of \"36 months\""},
        {"role": "user", "content": message},
      ]
  try:
    response = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages=original_messages,
      temperature=0.6,
    )
    # print(response)
    answer = response.choices[0].message.content.strip()
    # print(answer)
    prediction = predict_view(answer)
    response2 = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages=original_messages + [{"role": "user", "content": ""}, {"role": "system", "content": f"Do not return the JSON format. A trained model have predicted from the user input that the loan will be {prediction}. Relay this to the user and provide reasoning instead. If {prediction} is Fully paid, it means that the loan is likely to be approved, where as Charged off means the loan is likely to be rejected. Try to incorporate more financial jargon in your response. In addition, please provide suggestions as to how the user can increase the probability that their loan will be approved."}],
      temperature=0.6,
    )
    print(response2.choices)
    return response2.choices[0].message.content.strip()
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


def predict_view(json_string):
  module_dir = os.path.dirname(__file__)  # get current directory
  file_path_rf = os.path.join(module_dir, 'rf_model.joblib')
  file_path_encoder = os.path.join(module_dir, 'encoder1.joblib')
  try:
    encoder = joblib.load(file_path_encoder)
    # encoder = OneHotEncoder()
    model = joblib.load(file_path_rf)
    print(json_string)
    data = json.loads(json_string)
    data_dict = {key: [value] for key, value in data.items()}
    print(data_dict)
    new_input = pd.DataFrame(data_dict, index=[0])
    print(new_input)

    num_var=["loan_amnt","int_rate","annual_inc"]
    cat_var=["term","grade","purpose"]
    column_names = encoder.get_feature_names_out(cat_var)

    new_input_cat = new_input[cat_var]
    print(new_input_cat)
    new_input_num = new_input[num_var]
    new_input_encoded = encoder.transform(new_input_cat)

    new_input_encoded = pd.DataFrame(new_input_encoded.toarray(), columns=column_names)
    new_input_encoded = pd.concat([new_input_num.reset_index(drop=True), new_input_encoded.reset_index(drop=True)], axis=1)

    predictions = model.predict(new_input_encoded)
    print(predictions)
    return predictions[0]
  except:
    messages.warning(f"Error predicting loan approval, check your input data and try again.")
