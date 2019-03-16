FROM python:3.7-alpine as base
#---
FROM base as builder
RUN mkdir /install
WORKDIR /install

ADD requirements.txt .
# add compiler and postgres
RUN apk add build-base postgresql-dev py3-pillow
# pandas won't install without numpy being there first
RUN pip install --install-option="--prefix=/install" numpy==1.16.1
RUN pip install --install-option="--prefix=/install" -r requirements.txt

#---
FROM base
COPY --from=builder /install /usr/local

WORKDIR /app
RUN apk --no-cache add libpq py3-pillow

COPY * .
RUN ./manage.py collectstatic -l -c --noinput

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
