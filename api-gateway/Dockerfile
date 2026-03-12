FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

RUN mkdir -p /data/uploads /data/features /data/generated-tests

EXPOSE 4000

CMD ["node", "dist/main.js"]
