FROM yanchespenda/facerecognition-fastapi:latest

RUN pip3 install uvicorn gunicorn uvloop

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

# copy depencies project
COPY ./requirements.txt /

# install
RUN pip3 install -r requirements.txt

COPY ./app /app

WORKDIR /app/

ENV PYTHONPATH=/app

EXPOSE 80

# run project
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/start.sh"]
