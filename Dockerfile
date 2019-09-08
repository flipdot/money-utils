FROM python:3.7 as base

#---

FROM base as builder
RUN mkdir /install
WORKDIR /install

ADD requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
RUN useradd -m app && mkdir -p .env && ln -s /usr/local/bin .env/bin

COPY . ./
RUN ./manage.py collectstatic -l -c --noinput
USER app

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
