# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import apps, base64, requests
import os, string, random, glob
from flask import json
from werkzeug.utils import secure_filename
from apps.services.s3Manager.routes import s3_upload

def upload_file(file):
    print(file)
    filename = ''.join(random.choice(string.ascii_lowercase) for i in range(32)) + secure_filename(file.filename)
    apps.logger.info(filename)

    bucket_name='1779cloudcomputing'
    # s3_upload(bucket_name, file, filename)
    print(file)
    response = requests.post(apps.storageUrl + "/upload", files={"file": file}, data={"bucket": bucket_name, "filename": filename})

    print(response.content)
    return json.loads(response.content)["data"]

def removeAllImages():
    bucket_name='1779cloudcomputing'
    requests.post(apps.storageUrl + "/delete_images", data={"bucket": bucket_name})