# Aegis Frontend — Multi-stage Dockerfile
# Designed and Developed by NIKHIL CHARY SRIRAMOJU

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-slim AS runtime
LABEL maintainer="Nikhil Chary Sriramoju"
WORKDIR /app
RUN addgroup --system aegis && adduser --system --ingroup aegis aegis
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
USER aegis
EXPOSE 3000
CMD ["npm", "run", "start"]
