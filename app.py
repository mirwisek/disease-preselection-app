import json
import time
from mistralai import Mistral
import sounddevice as sd
import wavio
import numpy as np
import os
from utils import transcribe_audio, text_to_wav

import streamlit as st

class ChatBot:
    def __init__(self, api_key, history=None):
        self.api_key = api_key
        self.history = history if history is not None else [
            {
                "role": "system",
                "content": """
You are a medical assistant chatbot responsible for triaging patients as they arrive and generating a concise report to aid the doctor in prioritizing care.
On every user input you have the history of your past responses and the patient's responses.

# Instructions:
1. Ask up to five questions to quickly understand the patient's: 
    - main complaint.
    - the duration and progression of symptoms.
    - pain or discomfort level.
    - presence of any severe symptoms (such as chest pain or difficulty breathing).
    - presence of any other symptoms (such as fever, cough, or fatigue).
    - relevant medical background (medications, conditions).

2. Create a brief, clear report based on the patient’s responses, highlighting the key information that indicates the urgency of their condition.

# Constraints:
- ask only one question at a time.
- ask easy questions that a sick person can answer.
- be empathetic and professional.
- i need you to ask no more then five questions.
- generate a concise report when you are done.

# Output Format:
- Response format: JSON
    - when you want to ask a question, generate a JSON object with the key "question" and the value as the question you want to ask.
    - when you are done asking questions, generate a report with the key "report" and the value as this schema:
        - "main_complaint": "string"
        - "duration": "string"
        - "progression": "string"
        - "pain_level": "string"
        - "severe_symptoms": "string"
        - "other_symptoms": "string"
        - "medical_background"
        - "emergency_level": "string"

- No additional text, spaces, or explanations should be included.
        """,
            }
        ]
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-large-latest"

    def get_response(self, question, retries=3, delay=1):

        for _ in range(retries):
            try:
                chat_response = self.client.chat.complete(
                    model=self.model,
                    messages=self.history + [{"role": "user", "content": question}],
                    response_format = {
                        "type": "json_object",
                    }
                )
            except Exception as e:
                if "429" in str(e):
                    time.sleep(delay)
                    delay *= 2 
                else:
                    raise e

        self.history.append({"role": "user", "content": question})

        bot_message = chat_response.choices[0].message
        self.history.append({"role": bot_message.role, "content": bot_message.content})

        try:
            return json.loads(bot_message.content)
        except json.JSONDecodeError:
            return {
                "question": bot_message.content
            }


api_key = "POVQ5Fl6l3k7ODsPuNjSgJwAxr3Svqmz"

DURATION = 5  # Duration of the recording
SAMPLE_RATE = 16000  # Sample rate for audio recording
MAX_DURATION = 5 * 60  # Maximum duration for recording (in seconds)
WAVE_OUTPUT_FILE = "recorded_audio.wav"  # Output file for recorded audio
detected_lang = 'en-US'

# Function to start recording audio
def start_recording(sample_rate, max_duration):
    """Start recording audio and store it in session state."""
    st.session_state.recording = sd.rec(int(max_duration * sample_rate), samplerate=sample_rate, channels=1)
    st.session_state.is_recording = True

# Function to stop recording and save audio to file
def stop_recording(output_file, sample_rate):
    """Stop recording and save audio to file, trimming to the actual recording length."""
    sd.stop()
    st.session_state.is_recording = False
    st.session_state.has_recording = True

    # Trim the recording to the actual length recorded
    recording = st.session_state.recording
    recorded_length = np.where(recording != 0)[0][-1] + 1 if np.any(recording != 0) else 0
    trimmed_recording = recording[:recorded_length] if recorded_length > 0 else recording

    # Save the trimmed recording to the output file
    if recorded_length > 0:
        wavio.write(output_file, trimmed_recording, sample_rate, sampwidth=2)
        recorded_duration_seconds = recorded_length / sample_rate
        st.session_state.is_long_audio = recorded_duration_seconds >= 60
    else:
        st.session_state.is_long_audio = False
        st.session_state.has_recording = False
        st.error("No audio was recorded. Please try again.")


# Define the ask function (replace this with your actual implementation)
def ask(user_input, chatbot):
    # print(chatbot.history)
    chatbot_response = chatbot.get_response(user_input)
    # This is a mock implementation. Replace it with your actual function logic.
    if "report" in chatbot_response:
        return chatbot_response
    else:
        return chatbot_response
    

if __name__ == "__main__":
    import streamlit as st
    import json
    
    initial_question = "Hey, what brings you here today?"

    # Initialize session state to keep track of inputs
    if 'inputs' not in st.session_state:
        st.session_state.inputs = []
        # Add the initial question to the session state
        st.session_state.inputs.append(initial_question)
        st.session_state.chatbot = ChatBot(api_key)
        st.session_state.output_history = ""
        st.session_state.report = None

    # Initialize session state to keep track of recording state
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
        st.session_state.recording = None
        st.session_state.has_recording = False # Show transcript if the audio is already recorded

    st.title("Interactive Questioning App")

    # Function to handle user input and response
    def handle_input(output_box, user_input):
        
        st.session_state.inputs.append(user_input)
        st.session_state.output_history += '\n\n' + user_input
        output_box.markdown(st.session_state.output_history)

        response = ask(user_input, st.session_state.chatbot)

        if "question" in response:
            st.session_state.inputs.append(response["question"])
            st.session_state.output_history += '\n\n' + f'Question: {response["question"]}'
            output_box.markdown(st.session_state.output_history)
            audio_out_file = text_to_wav("Standard-A", response["question"], language_code=detected_lang)
                # Play the recorded audio
            if os.path.exists(audio_out_file):
                st.audio(audio_out_file, format='audio/wav', autoplay=True)

        elif "report" in response:
            st.session_state.report = response["report"]
            st.session_state.output_history += '\n\n' + f'Report: {response["report"]}'
            output_box.markdown(st.session_state.output_history)
            text_to_wav("Neural2-A", response["report"], language_code=detected_lang)


    output_txt_box = st.empty()

    st.text_input(f"Enter your answer here...", key=f"input")

    if st.session_state.output_history:
        outputs = st.markdown(st.session_state.output_history)
    else:
        outputs = st.markdown(f"Question: {initial_question}")

    if st.button(f"Submit Answer", key=f"button"):
        user_input = st.session_state[f"input"]
        handle_input(outputs, user_input)
        st.rerun()  # Rerun the app to update inputs

    btn_record = st.empty()

    # Toggle between "Record" and "Stop Recording" states
    if not st.session_state.is_recording:
        # If not recording, show the "Record" button
        if btn_record.button('Record'):
            start_recording(SAMPLE_RATE, MAX_DURATION)
            st.rerun()  # Immediately rerun to update the state

        if st.session_state.has_recording:
            # Transcribe the audio
            with st.spinner('Transcribing audio...'):
                transcripted_text, detected_lang = transcribe_audio(WAVE_OUTPUT_FILE, is_long_audio=st.session_state.is_long_audio)
                # voice_text_output.markdown(transcripted_text)
                handle_input(outputs, transcripted_text)
        
    else:
        # If recording, show the "Stop Recording" button
        if btn_record.button('Stop Recording'):
            stop_recording(WAVE_OUTPUT_FILE, SAMPLE_RATE)
            st.rerun()  # Immediately rerun to update the state

    # Check if there are any inputs before accessing the last one
    if st.session_state.inputs:
        if st.session_state.report:
            st.success(st.session_state.report)



