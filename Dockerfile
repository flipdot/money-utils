# FROM python:3.11-alpine
# RUN --mount=type=cache,target=/var/cache/apk \
# 	apk update && apk add python3-dev gcc libc-dev libffi-dev g++ \
# RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
# RUN apk add --update --no-cache py3-numpy py3-pandas@testing

# We don't use alpine or -slim, because pandas is a pain to build on them.
FROM python:3.11@sha256:3b3706a90cb23f04fabb0d255824f9a70ceb46177041898133dd5a35f3a50f0a

COPY --from=ghcr.io/astral-sh/uv:0.10.8@sha256:88234bc9e09c2b2f6d176a3daf411419eb0370d450a08129257410de9cfafd2a /uv /uvx /bin/

WORKDIR /app
RUN useradd -m app && chown -R app: /app
USER app

COPY uv.lock pyproject.toml ./
ENV UV_LINK_MODE=copy
ENV UV_FROZEN=1
ENV UV_COMPILE_BYTECODE=1
RUN --mount=type=cache,uid=1000,gid=1000,target=/home/app/.cache/uv \
	uv sync --no-install-project

COPY --chown=app:app . ./

ARG SOURCE_COMMIT
RUN mkdir -p /app/data \
	&& chown -R app: /app/data \
	&& sed -i '/home=/d' uwsgi.ini \
	&& sed -i "s/version = subprocess.*/version = '${SOURCE_COMMIT}'/" /app/hbci_client.py

RUN cp config.example.py config.py && \
	uv run python ./manage.py collectstatic -c --noinput && \
	gzip -r -k -9 /app/static && \
	rm config.py

EXPOSE 5002
VOLUME ["/app/data"]
CMD ["./webserver"]
