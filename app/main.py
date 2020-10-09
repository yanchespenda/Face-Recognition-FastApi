import face_recognition
import os
import requests
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from validator_collection import checkers
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Header, File, status, HTTPException, UploadFile, Body
import json

app = FastAPI()
origins = [
    "http://localhost:3333",
    "http://localhost:8000",
    "http://localhost:3000",
    "https://api.absensi.project.arproject.web.id",
    "https://absensi.project.arproject.web.id"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
TEMP_DIR = os.getenv("TEMP_DIR") or 'tmp/'

# Dev
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

TOLERANCE = os.getenv("RECOG_TOLERANCE") or 0.5


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
        return file_path
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
        raise Exception("Download error")

def allowed_file(filename: str):
    return '.' in filename and \
       filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def return_index_error(resources: List, detail = False):
    if detail:
        ret_return = []
        for resource in resources:
            ret_return.append({
                "result": bool(False),
                "distance": float(1.0)
            })

        return {
            "result": bool(False),
            "detail": ret_return
        }
    else:
        return {
            "result": bool(False),
        }

@app.get("/")
def root():
    return {
        "message": "Hello, Face Recognition API. Created by Alfian Rikzandi"
    }

@app.post("/verify", status_code=200)
async def verify_file(authorization: str = Header(None), resources: List[UploadFile] = File(...), verify: UploadFile = File(...), detail: Optional[bool] = False):
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
        try:
            image_encode = face_recognition.face_encodings(image_resource)[0]
        except IndexError as e:
            return return_index_error(resources, detail)
        resources_image.append(image_encode)

    if not allowed_file(verify.filename):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verify image not valid",
        )

    verify_image = face_recognition.load_image_file(verify.file)
    try:
        verify_image = face_recognition.face_encodings(verify_image)[0]
    except IndexError as e:
        return return_index_error(resources, detail)

    ret = face_recognition.compare_faces(resources_image, verify_image, TOLERANCE)

    is_detail = False
    ret_return = []
    if detail in (True, 'true'):
        is_detail = True
        ret_pros = face_recognition.face_distance(resources_image, verify_image)

        for i, face_distance in enumerate(ret_pros):

            ret_return.append({
                "result": bool(ret[i]),
                "distance": float(face_distance)
            })

    final_result = False
    for result in ret:
        if result:
            final_result = result

    if is_detail is False:
        return_json = {
            "result": bool(final_result)
        }
    else:
        return_json = {
            "result": bool(final_result),
            "detail": ret_return
        }

    return return_json


@app.post("/verify/url", status_code=200)
async def verify_url(authorization: str = Header(None), resources: List[str] = Body(...), verify: str = Body(...), detail: Optional[bool] = False):
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

    # Verify jwt token
    try:
        decoded = jwt.decode(token, JWT_PUBLIC, algorithms=JWT_ALGORITHM)
    except:
        raise credentials_exception

    if decoded is None:
        raise credentials_exception

    if not checkers.is_url(verify) or not allowed_file(verify):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verify image not valid",
        )

    # Download verify image
    try:
        verify_dir = download(verify, dest_folder=TEMP_DIR)
    except:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to download verify image",
        )

    verify_image = face_recognition.load_image_file(verify_dir)
    try:
        verify_image = face_recognition.face_encodings(verify_image)[0]
    except IndexError as e:
        return return_index_error(resources, detail)

    # Download resources image
    resources_image = []
    resources_temp = []
    for resource in resources:
        if not checkers.is_url(resource) or not allowed_file(resource):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resource image not valid",
            )

        try:
            resource_dir = download(resource, dest_folder=TEMP_DIR)
        except:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to download resource image",
            )

        image_resource = face_recognition.load_image_file(resource_dir)
        try:
            image_encode = face_recognition.face_encodings(image_resource)[0]
        except IndexError as e:
            return return_index_error(resources, detail)
        resources_image.append(image_encode)
        resources_temp.append(resource_dir)

    ret = face_recognition.compare_faces(resources_image, verify_image, TOLERANCE)

    is_detail = False
    ret_return = []
    if detail in (True, 'true'):
        is_detail = True
        ret_pros = face_recognition.face_distance(resources_image, verify_image)

        for i, face_distance in enumerate(ret_pros):
            ret_return.append({
                "result": bool(ret[i]),
                "distance": float(face_distance)
            })

    final_result = False
    for result in ret:
        if result:
            final_result = result

    # Clean up tmp downloads
    os.remove(verify_dir)
    for resource in resources_temp:
        os.remove(resource)

    if is_detail is False:
        return_json = {
            "result": bool(final_result)
        }
    else:
        return_json = {
            "result": bool(final_result),
            "detail": ret_return
        }

    return return_json

