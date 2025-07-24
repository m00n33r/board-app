# --- Этап 1: Сборка проекта (Build Stage) ---
# Используем легковесный образ Node.js v18
FROM node:18-alpine AS build

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы для установки зависимостей
COPY package.json pnpm-lock.yaml ./

# Устанавливаем зависимости с помощью pnpm
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Копируем все остальные файлы проекта
COPY . .

# Собираем Nuxt-приложение для продакшена
RUN pnpm nuxt build


# --- Этап 2: Запуск приложения (Production Stage) ---
# Начинаем с чистого и такого же легковесного образа
FROM node:18-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только собранные артефакты из этапа сборки
COPY --from=build /app/.output ./.output
# Копируем node_modules, необходимые для запуска сервера
COPY --from=build /app/node_modules ./node_modules

# Устанавливаем переменные окружения для продакшена
# HOST 0.0.0.0 обязателен, чтобы приложение было доступно извне контейнера
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Сообщаем Docker, что приложение слушает порт 3000
EXPOSE 3000

# Команда для запуска Nuxt-сервера
CMD ["node", ".output/server/index.mjs"]