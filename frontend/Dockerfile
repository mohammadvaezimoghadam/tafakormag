ARG REGISTRY=""

# ============================================
# Stage 1: development (Local Dev with HMR)
# ============================================
FROM ${REGISTRY}node:22-alpine AS development

WORKDIR /app

ARG NPM_REGISTRY="https://registry.npmmirror.com"

COPY package*.json ./
RUN ( \
      echo "Using fast npm mirror: ${NPM_REGISTRY}..." && \
      npm config set registry ${NPM_REGISTRY} && \
      sed -i "s|https://registry.npmjs.org/|${NPM_REGISTRY}/|g" package-lock.json && \
      sed -i "s|https://npm.devneeds.ir/repository/npm/|${NPM_REGISTRY}/|g" package-lock.json && \
      (npm ci --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund) \
    ) || ( \
      echo "Fast mirror failed, falling back to official npmjs registry..." && \
      npm config set registry https://registry.npmjs.org && \
      sed -i "s|${NPM_REGISTRY}/|https://registry.npmjs.org/|g" package-lock.json && \
      (npm ci --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund) \
    )

COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ============================================
# Stage 2: build (Production build)
# ============================================
FROM ${REGISTRY}node:22-alpine AS build

WORKDIR /app

ARG NPM_REGISTRY="https://registry.npmmirror.com"

COPY package*.json ./
RUN ( \
      echo "Using fast npm mirror: ${NPM_REGISTRY}..." && \
      npm config set registry ${NPM_REGISTRY} && \
      sed -i "s|https://registry.npmjs.org/|${NPM_REGISTRY}/|g" package-lock.json && \
      sed -i "s|https://npm.devneeds.ir/repository/npm/|${NPM_REGISTRY}/|g" package-lock.json && \
      (npm ci --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund) \
    ) || ( \
      echo "Fast mirror failed, falling back to official npmjs registry..." && \
      npm config set registry https://registry.npmjs.org && \
      sed -i "s|${NPM_REGISTRY}/|https://registry.npmjs.org/|g" package-lock.json && \
      (npm ci --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund) \
    )

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