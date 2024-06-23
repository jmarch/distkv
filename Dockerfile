FROM python:alpine

EXPOSE 8000

RUN mkdir /distkv

COPY ./requirements.txt /distkv/requirements.txt
COPY ./distkv /distkv/distkv
COPY ./scripts /distkv/scripts
COPY ./setup.py /distkv/setup.py

WORKDIR /distkv
RUN pip install -r requirements.txt
RUN pip install -e .

CMD ["distkv", "cluster1", "8000"]

