# FROM python:3.11-alpine
# RUN --mount=type=cache,target=/var/cache/apk \
# 	apk update && apk add python3-dev gcc libc-dev libffi-dev g++ \
# RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
# RUN apk add --update --no-cache py3-numpy py3-pandas@testing

# We don't use alpine or -slim, because pandas is a pain to build on them.
FROM python:3.11

RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /app
RUN useradd -m app && chown -R app: /app
USER app

COPY poetry.lock pyproject.toml ./
RUN mkdir -p /home/app/.cache/pypoetry/
RUN --mount=type=cache,uid=1000,gid=1000,target=/home/app/.cache/pypoetry/cache \
	--mount=type=cache,uid=1000,gid=1000,target=/home/app/.cache/pypoetry/artifacts \
	poetry install

COPY --chown=app:app . ./

ARG SOURCE_COMMIT
RUN mkdir -p /app/data \
	&& chown -R app: /app/data \
	&& sed -i '/home=/d' uwsgi.ini \
	&& sed -i "s/version = subprocess.*/version = '${SOURCE_COMMIT}'/" /app/hbci_client.py

RUN cp config.example.py config.py && \
	poetry run python ./manage.py collectstatic -c --noinput && \
	gzip -r -k -9 /app/static && \
	rm config.py

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
