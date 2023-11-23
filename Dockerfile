# -*- mode: Dockerfile -*-

FROM ghcr.io/feelpp/feelpp:jammy

USER root
COPY . /home/feelpp/
RUN ls -lrtR /home/feelpp

RUN dpkg -i /home/feelpp/*.deb 

USER feelpp

