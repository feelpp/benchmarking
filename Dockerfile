# -*- mode: Dockerfile -*-

FROM python:3.8

RUN pip install --upgrade pip

COPY . .
RUN python -m pip install -r requirements.txt

