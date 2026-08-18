FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY server.js handler.js ./
# uid of the image's node user, numeric so runAsNonRoot can verify it
USER 1000
EXPOSE 3000
CMD ["node", "server.js"]
