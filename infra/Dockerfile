# Один образ на оба процесса (бот и API) — они делят код и базу.
# Команда по умолчанию — бот; API поднимается тем же образом с своим CMD
# (см. infra/docker-compose.yml).
FROM python:3.12-slim-bookworm@sha256:0f5b26b9518d002b6173fd61daad821fa340635ebfec5bba471013f9ca114579

# Системные библиотеки: cairo/pango нужны WeasyPrint (PDF-разборы),
# libjpeg/zlib — Pillow (карточки для сторис). tzdata нужен zoneinfo:
# без него планировщик не сможет посчитать «9 утра по её таймзоне».
RUN apt-get update && apt-get install -y --no-install-recommends \
        tzdata \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
        libffi8 shared-mime-info \
        libjpeg62-turbo zlib1g \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/oracle

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY miniapp ./miniapp
COPY admin ./admin
COPY scripts ./scripts

# Пишем только в data/ — остальное дерево может быть read-only
RUN useradd --create-home --uid 10001 oracle \
    && mkdir -p /opt/oracle/data \
    && chown -R oracle:oracle /opt/oracle
USER oracle

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/opt/oracle/data

CMD ["python", "-m", "app.bot.main"]
