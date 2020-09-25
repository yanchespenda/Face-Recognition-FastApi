import face_recognition
# import os
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

# DIR_FACE = 'storage'
# DIR_TEMP_FACE = 'temp'
TOLERANCE = 0.6
# FRAME_THICKNESS = 3
# FONT_THICKNESS = 2
# MODEL = "cnn"

# known_faces = []
# known_names = []
# for name in os.listdir(DIR_FACE):
#     for filename in os.listdir(f"{DIR_FACE}/{name}"):
#         image = face_recognition.load_image_file(f"{DIR_FACE}/{name}/{filename}")
#         encoding = face_recognition.face_encodings(image)
#         known_faces.append(encoding)
#         known_names.append(name)


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

    if token not in ["iniToken"]:
        raise credentials_exception

    # if prosess in [None, ""]:
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #         detail="Process query missing",
    #     )

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

