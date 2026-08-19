FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
# The base image vendors the whole npm CLI dependency tree; a runtime image only needs `node`,
# so drop npm once the install is done instead of shipping its transitive CVEs.
RUN npm ci --omit=dev \
 && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /root/.npm
COPY server.js handler.js ./
# uid of the image's node user, numeric so runAsNonRoot can verify it
USER 1000
EXPOSE 3000
CMD ["node", "server.js"]
