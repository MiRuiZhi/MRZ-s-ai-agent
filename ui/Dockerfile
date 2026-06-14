FROM node:20-alpine AS build

WORKDIR /app
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN corepack enable \
    && corepack prepare pnpm@10.25.0 --activate \
    && pnpm install --frozen-lockfile
COPY ui ./
ARG SERVICE_BASE_URL=/api-proxy
ARG REACTOR_TOOL_BASE_URL=/tool
ENV SERVICE_BASE_URL=${SERVICE_BASE_URL}
ENV REACTOR_TOOL_BASE_URL=${REACTOR_TOOL_BASE_URL}
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
