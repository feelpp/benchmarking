FROM ubuntu:jammy

RUN apt-get update && apt-get install -y \
        python3 \
        python3-pip \
        wget

RUN wget -qO - http://apt.feelpp.org/apt.gpg | apt-key add
RUN echo "deb http://apt.feelpp.org/ubuntu/jammy jammy latest" | tee -a /etc/apt/sources.list.d/feelpp.list
RUN apt update

RUN apt-get update && apt-get install -y \
        libfeelpp1 \
        feelpp-tools \
        feelpp-quickstart \
        python3-feelpp \
        feelpp-data \
        libfeelpp-toolboxes1 \
        libfeelpp-toolboxes1-all-dev \
        feelpp-toolboxes \
        feelpp-toolboxes-data