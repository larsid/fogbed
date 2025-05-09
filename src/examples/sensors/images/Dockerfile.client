FROM ubuntu:focal

RUN apt-get update \
    # Install dependencies
    && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 \
    curl \
    wget \
    # Install NodeJS
    && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    # Install Application
    && wget https://github.com/EsauM10/covid-monitor/archive/main.tar.gz \
    && tar -xvzf main.tar.gz \
    && cp -a covid-monitor-main/  app/ \
    && rm -rf main.tar.gz \
    && rm -rf covid-monitor-main \
    && apt-get autoremove -y


WORKDIR /app

RUN npm install 

EXPOSE 3000

ENTRYPOINT [ "npm", "start" ]