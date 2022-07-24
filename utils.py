import hashlib
import io

from firebase_admin import credentials, initialize_app, storage

import config

credential_object = credentials.Certificate("./credentials.json")
initialize_app(
    credential=credential_object,
    options={"storageBucket": f"{config.bucket_name}.appspot.com"},
)


def upload_to_cloud(file: io.BytesIO) -> str:
    """
    Handler to upload files to cloud storage.
    """
    bucket = storage.bucket()
    file_hash = hashlib.md5(file.getbuffer())
    audioFile = bucket.blob(f"{file_hash.hexdigest()}.wav")
    try:
        audioFile.upload_from_file(file)
    except:
        print("Error occured while uploading file to cloud.")
        return

    audioFile.make_public()
    return audioFile.media_link
