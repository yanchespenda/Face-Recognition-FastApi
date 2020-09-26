import face_recognition
import os
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
# import cv2
# import urllib.request
# from skimage import io
# import numpy as np


# Web Server
# from typing import Optional
from typing import List
from fastapi import FastAPI, Header, File, status, HTTPException, UploadFile

app = FastAPI()

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']

# Develop Only
public_raw_key = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzIe8CRIuNCFx6CufYA6R
K0vR3hnlMG+Xbdg48mYH2rPqR4Eg4mVjLRMQlvCM5AQBkdd3aWvVV3/1n1hdGhRI
AHfaI/WR5x/reDgxCFaQ1tc6sLqrt8ObdrIVmmxqT1sl+eoUdQC91mfD4Qat/ea6
PMcqyFPu1u0+Ht10Mmi5eErX7meuGYqGU28W0ZOZXrq1dhHe1xZzb+XwvepGgWcd
v3mG1g7vayz0kLgcnO7eVWhDBtPPrL2uGssi5TZC+MYxEBEeOeybV/0onOG8p7og
5Q7ua+xk+u3GG/CnuHhXLLXKygDrf7EtQoSmf0FX0O20Z16Fp25+EF4b/Qy9AG9Y
9wIDAQAB
-----END PUBLIC KEY-----
"""
JWT_PUBLIC = serialization.load_pem_public_key(public_raw_key, backend=default_backend())
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or 'RS256'
# JWT_SECRET = os.getenv("JWT_SECRET")

TOLERANCE = 0.6


def allowed_file(filename: str):
    return '.' in filename and \
       filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.get("/")
def read_root():
    return {
        "message": "Hello, Face Recognition API. Created by Alfian Rikzandi"
    }

@app.post("/verify", status_code=200)
async def read_item(authorization: str = Header(None), resources: List[UploadFile] = File(...), verify: UploadFile = File(...)):
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identity, token = authorization.split(' ')
    if identity not in "Bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bearer authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    decoded = None
    try:
        decoded = jwt.decode(token, JWT_PUBLIC, algorithms=JWT_ALGORITHM)
    except:
        raise credentials_exception

    if decoded is None:
        raise credentials_exception

    resources_image = []
    for file in resources:
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resources image not valid",
            )

        image_resource = face_recognition.load_image_file(file.file)
        image_encode = face_recognition.face_encodings(image_resource)[0]
        resources_image.append(image_encode)

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verify image not valid",
        )

    verify_image = face_recognition.load_image_file(verify.file)
    verify_image = face_recognition.face_encodings(verify_image)[0]

    ret = face_recognition.compare_faces(resources_image, verify_image, TOLERANCE)
    ret_pros = face_recognition.face_distance(resources_image, verify_image)

    print(ret, ret_pros)

    final_result = False
    for result in ret:
        if result:
            final_result = result

    return {
        "message": "Success",
        "result": bool(final_result)
    }

