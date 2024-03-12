FROM python:3.11-alpine
#FROM python:3.8-slim

# for alpine:
RUN --mount=type=cache,target=/var/cache/apk \
	apk update && apk add python3-dev gcc libc-dev libffi-dev

RUN mkdir /install
WORKDIR /install

RUN pip install --no-cache-dir poetry==1.8.2

COPY poetry.lock pyproject.toml ./
RUN --mount=type=cache,target=/home/.cache/pypoetry/cache \
	--mount=type=cache,target=/home/.cache/pypoetry/artifacts \
	poetry install

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
