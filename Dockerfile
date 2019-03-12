FROM python:3.7-alpine

WORKDIR /app
ADD requirements.txt .
RUN apk add build-base postgresql-client
RUN pip install numpy==1.16.1 #???
RUN pip install -r requirements.txt

ADD * .

RUN ./manage.py collectstatic -l -c --noinput

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
