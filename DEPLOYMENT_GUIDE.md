# 🚀 Руководство по деплою board-app

## ❌ Проблема: Ошибка 502 Bad Gateway

### 🔍 **Основные причины ошибки 502:**

1. **Переменные окружения не попадают в контейнер**
   - ❌ `.env` файл был исключен из Docker образа
   - ✅ **Исправлено**: Убрали `.env` из `.dockerignore`

2. **Отсутствует healthcheck**
   - ❌ Docker не знает, когда сервис готов
   - ✅ **Исправлено**: Добавили healthcheck для web и bot сервисов

3. **Проблемы с портами**
   - ❌ Приложение может не слушать нужный порт
   - ✅ **Исправлено**: Явно указали HOST=0.0.0.0 и PORT=3000

## 🛠️ **Исправления, которые были внесены:**

### 1. **`.dockerignore`**
```diff
- .env
+ # .env
```

### 2. **`docker-compose.yml`**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. **`Dockerfile`**
```dockerfile
# Устанавливаем wget для healthcheck
RUN apk add --no-cache wget

# Создаем пользователя для безопасности
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nuxt -u 1001
RUN chown -R nuxt:nodejs /app
USER nuxt
```

### 4. **Добавлены API endpoints**
- `/api/health` - для healthcheck
- `/api/debug` - для отладки (только в dev режиме)

## 🚀 **Инструкция по деплою:**

### 1. **Подготовка**
```bash
# Убедитесь, что .env файл содержит все необходимые переменные
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_SERVICE_KEY=...
NUXT_PUBLIC_TELEGRAM_APP_URL=...
TELEGRAM_BOT_TOKEN=...
```

### 2. **Сборка и запуск**
```bash
# Остановить существующие контейнеры
docker-compose down

# Удалить старые образы
docker-compose down --rmi all

# Пересобрать и запустить
docker-compose up --build -d
```

### 3. **Проверка логов**
```bash
# Логи web сервиса
docker-compose logs -f web

# Логи bot сервиса
docker-compose logs -f bot

# Общие логи
docker-compose logs -f
```

### 4. **Проверка статуса**
```bash
# Статус сервисов
docker-compose ps

# Healthcheck статус
docker-compose exec web wget --no-verbose --tries=1 --spider http://localhost:3000/api/health
```

## 🔧 **Дополнительные настройки для продакшена:**

### **Nginx конфигурация (если используется):**
```nginx
upstream board_app {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://board_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты для больших запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### **Systemd сервис (если не используете Docker Compose):**
```ini
[Unit]
Description=Board App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/board-app
Environment=NODE_ENV=production
ExecStart=/usr/bin/node .output/server/index.mjs
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🚨 **Частые проблемы и решения:**

### **Проблема: "Cannot find module"**
```bash
# Решение: Пересобрать образ
docker-compose down --rmi all
docker-compose up --build -d
```

### **Проблема: "Permission denied"**
```bash
# Решение: Проверить права на файлы
chmod -R 755 .
chown -R $USER:$USER .
```

### **Проблема: "Port already in use"**
```bash
# Решение: Освободить порт
sudo lsof -ti:3000 | xargs kill -9
```

## 📊 **Мониторинг:**

### **Проверка ресурсов:**
```bash
# Использование памяти и CPU
docker stats

# Размер образов
docker images
```

### **Логи приложения:**
```bash
# В реальном времени
docker-compose logs -f --tail=100
```

## ✅ **После исправлений:**

1. **Переменные окружения** попадают в контейнер ✅
2. **Healthcheck** проверяет готовность сервиса ✅
3. **Безопасность** улучшена (non-root пользователь) ✅
4. **Мониторинг** добавлен ✅

## 🆘 **Если проблема остается:**

1. **Проверьте логи**: `docker-compose logs -f`
2. **Проверьте переменные**: `docker-compose exec web env | grep SUPABASE`
3. **Проверьте healthcheck**: `docker-compose ps`
4. **Проверьте порты**: `netstat -tlnp | grep 3000`

---

**Автор**: AI Assistant  
**Дата**: $(date)  
**Версия**: 1.0
