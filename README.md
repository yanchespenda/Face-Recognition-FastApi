## Face Recognition - Verify API
Compare face from known image to unknown image

### Installation
Tested on python 3.8
```
pip install -r requirements.txt
```


### How to run
```
cd app
uvicorn app.main:app --reload
```

### Endpoint API
```
/verify [POST]
```

| Body       | Type             | Description                           |
|------------|------------------|---------------------------------------|
| resources  | fileupload       | Resource face (known face)            |
| verify     | fileupload       | Verify face (unkown face)             |

```
/verify/url [POST]
```

| Body (JSON) | Type             | Description                           |
|-------------|------------------|---------------------------------------|
| resources   | string (url)     | Resource face (known face)            |
| verify      | string (url)     | Verify face (unkown face)             |

