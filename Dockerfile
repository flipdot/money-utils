FROM python:3.7 as base

#---

FROM base as builder
RUN mkdir /install
WORKDIR /install

ADD requirements.txt .
RUN pip install --install-option="--prefix=/install" -r requirements.txt

#---
FROM base
COPY --from=builder /install /usr/local
WORKDIR /app

RUN mkdir -p .env && ln -s /usr/local/bin .env/bin
#RUN apk --no-cache add libpq

COPY . ./
RUN ./manage.py collectstatic -l -c --noinput

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
