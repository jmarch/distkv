FROM python:3-slim

RUN apt-get update && apt-get install -y gcc libev-dev && apt-get clean && apt-get autoclean

RUN mkdir /distkv

WORKDIR /distkv

COPY ./distkv distkv
COPY ./scripts scripts
COPY ./setup.py setup.py
COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --no-dependencies -r requirements.txt
RUN pip install -e .

EXPOSE 8000
CMD ["distkv", "cluster1", "8000"]

