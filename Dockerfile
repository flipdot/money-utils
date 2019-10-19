FROM python:3.7

RUN mkdir /install
WORKDIR /install

ADD requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
RUN useradd -m app && mkdir -p .env && ln -s /usr/local/bin .env/bin

COPY . ./
RUN mkdir -p /app/data \
	&& chown app: /app/data \
	&& sed -i '/home=/d' uwsgi.ini \
	&& sed -i "s/version = subprocess.*/version = $(echo "$SOURCE_COMMIT" | cut -c-5)/" hbci_client.py

RUN cp config.example.py config.py && ./manage.py collectstatic -l -c --noinput && rm config.py
USER app

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
