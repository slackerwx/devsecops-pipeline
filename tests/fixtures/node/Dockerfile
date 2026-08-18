FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY server.js handler.js ./
USER node
EXPOSE 3000
CMD ["node", "server.js"]
