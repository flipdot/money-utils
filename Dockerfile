FROM ghcr.io/astral-sh/uv:python3.11-bookworm

RUN apt update
RUN apt install build-essential python3-dev -y
RUN apt install nano vim tree -y

WORKDIR /app
RUN useradd -m app && chown -R app: /app

COPY --chown=app:app uv.lock /app/
COPY --chown=app:app pyproject.toml /app/
RUN uv sync --no-install-project
COPY --chown=app:app . /app/
RUN uv sync --package money-utils

# RUN mkdir -p /app/volumes
# RUN chown -R app: /app/volumes

#	&& sed -i '/home=/d' uwsgi.ini \
#	&& sed -i "s/version = subprocess.*/version = '${SOURCE_COMMIT}'/" /app/hbci_client.py

#RUN uv run ./manage.py collectstatic -c --noinput

#RUN gzip -r -k -9 /app/static

EXPOSE 5002
# VOLUME ["/app/volumes"]

CMD ["uv", "run", "scripts/webserver"]
# CMD ["/bin/bash"]
