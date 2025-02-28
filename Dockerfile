# -*- mode: Dockerfile -*-

FROM python:3.8

RUN pip install build

COPY . .
RUN python -m pip install .

