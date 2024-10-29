FROM node:18

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# This runs both commands
CMD npm run watch & npm run serve & wait
