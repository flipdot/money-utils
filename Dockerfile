FROM python:3.8

RUN mkdir /install
WORKDIR /install

ADD requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
RUN useradd -m app && mkdir -p .env && ln -s /usr/local/bin .env/bin

COPY . ./

ARG SOURCE_COMMIT
RUN mkdir -p /app/data \
	&& chown -R app: /app/data \
	&& sed -i '/home=/d' uwsgi.ini \
	&& sed -i "s/version = subprocess.*/version = '${SOURCE_COMMIT}'/" /app/hbci_client.py

RUN cp config.example.py config.py && \
	./manage.py collectstatic -c --noinput && \
	gzip -r -k -9 /app/static && \
	rm config.py
USER app

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
