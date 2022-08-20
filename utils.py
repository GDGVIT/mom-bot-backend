import hashlib
import io
import speech_recognition as sr
from os import system
import discord
import config

import config
from google.cloud.storage.bucket import Blob
from firebase_admin import credentials, initialize_app, storage

credential_object = credentials.Certificate("./credentials.json")
initialize_app(
    credential=credential_object,
    options={"storageBucket": f"{config.bucket_name}.appspot.com"},
)


def upload_recording_to_cloud() -> Blob:
    """
    Handler to upload files to cloud storage.
    """
    with open("full_record.wav", "rb") as file:
        bucket = storage.bucket()
        file_hash = hashlib.md5(file.read())
        audio_file = bucket.blob(f"{file_hash.hexdigest()}.wav")
        try:
            audio_file.upload_from_filename("full_record.wav")
        except:
            print("Error occured while uploading file to cloud.")
            return None

        audio_file.make_public()
        return audio_file


def save_all_audio(sink: discord.sinks.WaveSink) -> None:
    for user in sink.audio_data.keys():
        # writes each file to disk
        with open(f"{user}.wav", "wb") as file:
            file.write(sink.audio_data[user].file.getvalue())

        # Resample to 1 channel, 16kHz sample rate and dither to 16 bit depth 
        # for compatibility with voice API
        system(
            f"sox --ignore-length {user}.wav -c 1 -r 16000 -b 16 {user}_processed.wav"
        )
        system(f"rm -rf {user}.wav")


def get_transcription(file: str, start_time: float, duration: float) -> str:
    # returns the transcript for a particular time
    r = sr.Recognizer()
    system("rm -rf tmp.wav")
    system(f"sox {file} tmp.wav trim {start_time} {duration}")
    with sr.AudioFile("tmp.wav") as audio_file:
        system("sox --ignore-length full_record.wav tmp.wav full_audio.wav")
        system("mv full_audio.wav full_record.wav")
        audio = r.record(audio_file)
        try:
            return r.recognize_google(
                audio, language="en-IN", key=config.google_voice_key
            )
        except sr.UnknownValueError:
            return "?"

def cleanup_tmp() -> None:
    # cleans up all temporary files created during transcription
    system("rm -rf tmp.wav")
    system("rm -rf *_processed.wav")
    system("rm -rf transcript.txt")
    system("rm -rf summary.txt")
