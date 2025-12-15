# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
RUN mkdir -p /app/result_build && cp -r build/* /app/result_build/
