# Production frontend image for the Next.js app in frontend/.
# Multi-stage: install deps -> build -> minimal runtime stage.
#
# Build context is expected to be frontend/, e.g.:
#   docker build -f deployment/docker/frontend.Dockerfile -t <name> frontend
# (docker-compose.yml's "frontend" profile service is wired this way.)
#
# NOTE (repository audit finding, Phase 12): as of this Dockerfile's
# authoring, frontend/ is an empty scaffold - package.json has no
# name/dependencies/scripts and there is no lockfile yet, so this
# image cannot actually be built until real Next.js application code
# and a lockfile (package-lock.json) are added. The stages below are
# written to be correct for a standard Next.js app the moment that
# happens, using only the existing package.json/lockfile - nothing
# about the frontend's application code is invented here.

# ---------- deps ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time-only, public (non-secret) configuration baked into the
# client bundle - never pass secrets through NEXT_PUBLIC_* build args.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# ---------- runtime ----------
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public

USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["npm", "run", "start"]
