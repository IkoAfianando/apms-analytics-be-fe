FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && corepack prepare pnpm@8.15.4 --activate && pnpm install --frozen-lockfile

FROM node:18-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && pnpm build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY package.json .
RUN corepack enable && corepack prepare pnpm@8.15.4 --activate && pnpm install --prod --ignore-scripts --frozen-lockfile
EXPOSE 3000
CMD ["pnpm", "start"]

