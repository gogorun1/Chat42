FROM python:3.12-slim

# Non-root user matching the host dev machine's UID/GID, so files the
# container creates in the bind-mounted ./backend stay owned by the host user.
# Override at build time with --build-arg HOST_UID=$(id -u) --build-arg HOST_GID=$(id -g)
# if your UID/GID isn't the default (see root .env / .env.example).
ARG HOST_UID=1001
ARG HOST_GID=1001
RUN groupadd -g "$HOST_GID" appuser && useradd -m -u "$HOST_UID" -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
