FROM arm32v6/alpine:3.6

LABEL maintainer="Zane Mountcastle <zane@missionmule.com>"

# Update system dependencies
#RUN apt-get update && apt-get install -y \
#    wget \
#    dialog \
#    build-essential \
#    git \
#    python2.7 \
#    python-pip \
#    python-dev

# Update system dependencies
RUN apk add --update --no-cache --virtual \
    python python-dev libffi-dev make openssl build-base bash ca-certificates py2-pip \
#    && pip install --upgrade pip \
    && pip install virtualenv \
    && rm -rf /var/cache/apk/*

# Set working directory to `/data-mule`
WORKDIR /data-mule

# Copy current directory to `/data-mule`
ONBUILD ADD . /data-mule
ONBUILD RUN virtualenv /env && /env/bin/pip install -r /data-mule/requirements.txt

RUN apk del .pynacl_deps

# Use Python 2.7
FROM python:2.7

# Run the application
CMD ["python", "app.py"]