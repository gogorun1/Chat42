FROM node:20-alpine

# Non-root user matching the host dev machine's UID/GID, so files the
# container creates in the bind-mounted ./frontend stay owned by the host user.
# Override at build time with --build-arg HOST_UID=$(id -u) --build-arg HOST_GID=$(id -g)
# if your UID/GID isn't the default (see root .env / .env.example).
ARG HOST_UID=1001
ARG HOST_GID=1001
RUN addgroup -g "$HOST_GID" appuser && adduser -D -u "$HOST_UID" -G appuser appuser

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
