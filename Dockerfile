# syntax=docker/dockerfile:1
FROM python:3.9.8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
EXPOSE 8000 3333
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt
RUN python -m pip install --upgrade pip

COPY . /code/

CMD gunicorn plateRecognition.wsgi --bind 0.0.0.0:$PORT
