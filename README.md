# Nuxt.js Telegram Mini App

Telegram Mini App для просмотра и управления событиями.

## Исправленные проблемы

### 1. Ошибка 502 при деплое на хостинг
- Включен SSR в `nuxt.config.ts`
- Добавлен `nitro.preset: 'node-server'`
- Создан Dockerfile и docker-compose.yml
- Добавлен start скрипт в package.json

### 2. Проблемы с user_id в Telegram
- Создан composable `useTelegram` для корректной работы с Telegram WebApp
- Добавлен fallback для получения user_id из хэша URL
- Реализовано ожидание готовности Telegram WebApp
- Сохранение user_id в localStorage для fallback

### 3. Слайдбар с тегами
- Добавлен горизонтальный слайдбар с тегами под month-container
- Фильтрация событий по выбранным тегам
- Адаптивный дизайн для мобильных устройств
- API endpoint для загрузки тегов

## Установка и запуск

### Локальная разработка
```bash
npm install
npm run dev
```

### Docker деплой
```bash
# Создайте .env файл на основе .env.example
cp .env.example .env

# Заполните переменные окружения
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Запуск через Docker Compose
docker-compose up -d

# Или сборка и запуск Docker образа
docker build -t nuxt-app .
docker run -p 3000:3000 --env-file .env nuxt-app
```

## Структура проекта

```
├── components/          # Vue компоненты
│   └── SwipeCard.vue   # Основной компонент с карточками и тегами
├── composables/         # Vue composables
│   ├── useTelegram.ts  # Работа с Telegram WebApp
│   └── useCardBackground.ts
├── server/api/          # API endpoints
│   ├── tags.ts         # Загрузка тегов
│   ├── loadCard.ts     # Загрузка карточек с фильтрацией по тегам
│   └── ...
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose конфигурация
└── nuxt.config.ts      # Конфигурация Nuxt.js
```

## API Endpoints

### GET /api/tags
Загружает все доступные теги для фильтрации.

### POST /api/loadCard
Загружает карточки событий с поддержкой фильтрации по тегам.

**Параметры:**
- `eventId` - ID события
- `direction` - направление ('next', 'prev', 'current')
- `tagId` - ID тега для фильтрации (опционально)

## Переменные окружения

- `SUPABASE_URL` - URL вашей Supabase базы данных
- `SUPABASE_KEY` - Anon key для Supabase
- `NODE_ENV` - Окружение (development/production)
- `HOST` - Хост для приложения (0.0.0.0 для Docker)
- `PORT` - Порт для приложения (3000)

## Особенности

- Полная поддержка Telegram WebApp
- Fallback для получения user_id из хэша URL
- Фильтрация событий по тегам
- Адаптивный дизайн
- Docker контейнеризация
- SSR для production
