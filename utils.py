# Speech to Text
# from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as speech
from google.cloud import storage
# Text to Speech
from typing import Sequence
import google.cloud.texttospeech as tts
import os

PROJECT_ID = "mistral-alan-hack24par-821"

def _upload_audio_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads an audio file to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    # print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def _transcribe_audio_source(source_file_or_gcs_uri, is_long_audio=False, lang="en-US"):
    detected_lang = "en-US"
    """Transcribes the audio file from GCS using Google Speech-to-Text."""
    client = SpeechClient()

    # if is_long_audio: 
    #     audio = speech.RecognitionAudio(uri=source_file_or_gcs_uri)
    # else:
    with open(source_file_or_gcs_uri, "rb") as f:
        audio_content = f.read()
    # audio = speech.RecognitionAudio(content=audio_content)


    # config = speech.RecognitionConfig(
    #     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    #     # language_code=lang,
    #     language_codes=["en-US", "es-ES", "fr-FR"],
    # )
    config = speech.RecognitionConfig(
        auto_decoding_config=speech.AutoDetectDecodingConfig(),
        language_codes=["en-US", "fr-FR", "es-ES", "it-IT"],
        model="long",
    )

    request = speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        config=config,
        content=audio_content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)
    

    # Use long-running recognition for potentially longer audio files
    # if is_long_audio:
    #     operation = client.long_running_recognize(config=config, audio=audio)
    #     response = operation.result(timeout=90)
    # else:
    #     response = client.recognize(config=config, audio=audio)

    transcript = ""
    print(response)

    for result in response.results:
        detected_lang = result.language_code
        transcript += result.alternatives[0].transcript

    return transcript, detected_lang

def transcribe_audio(source_file_or_gcs_uri, is_long_audio=False):
    bucket_name = "mistral-hackathon-audios"  # Replace with your GCS bucket name
    destination_blob_name = "audio_sample.wav"  # Name to save as in GCS

    # if is_long_audio:
    #     # Upload the file to the GCS bucket
    #     _upload_audio_to_gcs(bucket_name, source_file_or_gcs_uri, destination_blob_name)
    #     # Transcribe the audio from GCS
    #     gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    #     return _transcribe_audio_source(gcs_uri, is_long_audio)
    # else:
    return _transcribe_audio_source(source_file_or_gcs_uri, is_long_audio)
    

def text_to_wav(voice_name: str, text: str, language_code: str = None):
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=language_code + '-' + voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    filename = f"{voice_name}.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Generated speech saved to "{filename}"')

    return filename


