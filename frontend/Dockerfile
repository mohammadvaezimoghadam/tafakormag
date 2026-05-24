ARG REGISTRY=""

# ============================================
# Stage 1: development (Local Dev with HMR)
# ============================================
FROM ${REGISTRY}node:22-alpine AS development

WORKDIR /app

COPY package*.json ./
RUN (sed -i 's|https://npm.devneeds.ir/repository/npm/|https://registry.npmjs.org/|g' package-lock.json && npm install) || \
    (echo "Primary npm registry failed/unreachable. Falling back to devneeds mirror..." && \
     sed -i 's|https://registry.npmjs.org/|https://npm.devneeds.ir/repository/npm/|g' package-lock.json && \
     npm install --registry=https://npm.devneeds.ir/)

COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ============================================
# Stage 2: build (Production build)
# ============================================
FROM ${REGISTRY}node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN (sed -i 's|https://npm.devneeds.ir/repository/npm/|https://registry.npmjs.org/|g' package-lock.json && npm install) || \
    (echo "Primary npm registry failed/unreachable. Falling back to devneeds mirror..." && \
     sed -i 's|https://registry.npmjs.org/|https://npm.devneeds.ir/repository/npm/|g' package-lock.json && \
     npm install --registry=https://npm.devneeds.ir/)

COPY . .

ARG VITE_API_BASE_URL=/
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

ARG VITE_BALE_OTP_BOT_URL=https://ble.ir/tafakor_otp_bot
ENV VITE_BALE_OTP_BOT_URL=$VITE_BALE_OTP_BOT_URL

RUN npm run build

# ============================================
# Stage 3: production (Nginx)
# ============================================
FROM ${REGISTRY}nginx:stable-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /app/staticfiles

CMD ["nginx", "-g", "daemon off;"]