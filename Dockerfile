# -*- mode: Dockerfile -*-

FROM python:3.13

RUN pip install build

COPY . .
RUN python -m pip install .

