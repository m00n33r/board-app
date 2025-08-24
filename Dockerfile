# Простой Dockerfile для Timeweb.cloud (один этап)
FROM node:18-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Устанавливаем pnpm и зависимости
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Копируем все файлы проекта
COPY . .

# Собираем Nuxt-приложение для продакшена
RUN pnpm nuxt build

# Устанавливаем переменные окружения для продакшена
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Сообщаем Docker, что приложение слушает порт 3000
EXPOSE 3000

# Простая команда запуска
CMD ["node", ".output/server/index.mjs"]