# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS builder

WORKDIR /app/frontend

ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_AUTH_COOKIE_NAME

ENV NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
    NEXT_PUBLIC_AUTH_COOKIE_NAME="${NEXT_PUBLIC_AUTH_COOKIE_NAME}" \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json ./
COPY frontend/package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm ci

COPY frontend ./

RUN npm run build
RUN npm prune --omit=dev


FROM node:22-bookworm-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

WORKDIR /app

RUN groupadd --system utw \
    && useradd --system --create-home --gid utw utw \
    && mkdir -p /app \
    && chown -R utw:utw /app

COPY --from=builder /app/frontend/package.json /app/package.json
COPY --from=builder /app/frontend/node_modules /app/node_modules
COPY --from=builder /app/frontend/.next /app/.next

USER utw

EXPOSE 3000

CMD ["node_modules/.bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
