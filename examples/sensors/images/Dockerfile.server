FROM ubuntu:focal

RUN apt-get update \ 
    && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 \
    python3 \
    pip \
    python3.8-venv \
    wget \
    && wget https://github.com/larsid/covid-api/archive/main.tar.gz \
    && tar -xvzf main.tar.gz \
    && cp -a covid-api-main/  app/ \
    && rm -rf main.tar.gz \
    && rm -rf covid-api-main \
    && apt-get autoremove


ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "app.py" ]
