# -*- mode: Dockerfile -*-

FROM python:3.13

COPY . .
RUN python -m pip install .