FROM python:3.9-alpine

ENV REDIS_HOST=redis

RUN apk update \
 && apk add gcc musl-dev libressl-dev libffi-dev

WORKDIR /usr/src/
COPY . /usr/src/
RUN chmod +x /usr/src/*_bot.py
RUN pip install -r /usr/src/requirements.txt
