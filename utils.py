from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
import os

def _upload_audio_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads an audio file to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    # print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def _transcribe_audio_source(source_file_or_gcs_uri, is_long_audio=False, lang="en-US"):
    """Transcribes the audio file from GCS using Google Speech-to-Text."""
    client = speech.SpeechClient()

    if is_long_audio: 
        audio = speech.RecognitionAudio(uri=source_file_or_gcs_uri)
    else:
        with open(source_file_or_gcs_uri, "rb") as f:
            audio_content = f.read()
        audio = speech.RecognitionAudio(content=audio_content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code=lang,
    )

    # Use long-running recognition for potentially longer audio files
    if is_long_audio:
        operation = client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=90)
    else:
        response = client.recognize(config=config, audio=audio)

    transcript = ""

    for result in response.results:
        transcript += result.alternatives[0].transcript

    return transcript

def transcribe_audio(source_file_or_gcs_uri, is_long_audio=False):
    bucket_name = "mistral-hackathon-audios"  # Replace with your GCS bucket name
    destination_blob_name = "audio_sample.wav"  # Name to save as in GCS

    if is_long_audio:
        # Upload the file to the GCS bucket
        _upload_audio_to_gcs(bucket_name, source_file_or_gcs_uri, destination_blob_name)
        # Transcribe the audio from GCS
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
        return _transcribe_audio_source(gcs_uri, is_long_audio)
    else:
        return _transcribe_audio_source(source_file_or_gcs_uri, is_long_audio)