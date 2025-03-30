FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install
# Install TypeScript type declarations
RUN npm install --save-dev @types/react @types/react-dom @types/react-router-dom

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 