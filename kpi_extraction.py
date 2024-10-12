import os
import pandas as pd
from mistralai import Mistral

# Mistral API setup
api_key = "Nj0pLNlrHtmzDGfmXzWjJjWqCD6af2dv"  # Replace with your actual API key
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

# Load the dataset using pandas
dataset_path = 'dataset/disease.csv'
df = pd.read_csv(dataset_path)

# Extract relevant data from the dataset to use as context
# Assuming the dataset has columns like 'Disease', 'Symptoms', 'Profile', etc.
# We will extract this information for a specific disease
disease_name = "diabetes"  # You can change this to another disease
disease_data = df[df['Disease'] == disease_name]

# Create context from the dataset: extracting symptoms and patient profiles
if not disease_data.empty:
    symptoms = disease_data['Symptoms'].values[0]  # Get the symptoms for the disease
    profile = disease_data['Profile'].values[0]    # Get the patient profile info for the disease
    
    # Format the context for Mistral
    context = f"Disease: {disease_name}\nSymptoms: {symptoms}\nPatient Profile: {profile}"
else:
    context = f"No data available for the disease: {disease_name}"

# Define the Mistral prompt with the extracted context
mistral_prompt = f"Based on the following medical data, generate key diagnostic questions for a doctor to ask a patient to pre-classify the disease:\n\n{context}\n\nKPIs:"

# Make the API call to Mistral to generate diagnostic questions
chat_response = client.chat.complete(
    model=model,
    messages=[
        {
            "role": "user",
            "content": mistral_prompt,
        },
    ]
)

# Print the response from Mistral (the generated KPIs)
print(chat_response.choices[0].message.content)
