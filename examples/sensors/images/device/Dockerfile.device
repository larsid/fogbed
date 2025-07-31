FROM ubuntu:focal

RUN apt-get update \
    && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 \
    python3 \
    pip \
    python3.8-venv \
    && apt-get autoremove

# Use a virtual environment to avoid running pip as root
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
