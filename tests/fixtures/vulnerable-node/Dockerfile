FROM node:latest
WORKDIR /app
ADD . /app
RUN npm install --omit=dev
EXPOSE 3000
CMD ["node", "server.js"]
