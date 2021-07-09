# syntax=docker/dockerfile:1
FROM python:3.8


COPY STGB_backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir /database
RUN mkdir /utils
COPY ../database /database
COPY ../config.py config.py
COPY ../utils /utils

COPY /STGB_backend /STGB_backend
WORKDIR STGB_backend

