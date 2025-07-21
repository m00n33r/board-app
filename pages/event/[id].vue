<template>
  <div class="event-page-wrapper" :style="{ background: gradientBackgroundColor }">
    <div v-if="event" class="event-page">
      <div class="card-container">
        <div class="card">
          <img :src="event.event_banner" alt="Event Banner" class="card-image" />
        </div>
      </div>

      <h1 class="event-title">{{ event.event_name }}</h1>
      <p class="event-date">
        {{ capitalizeMonth(event.event_date) }}, {{ event.event_time }} GMT+3
      </p>

      <div class="event-actions">
        <button
          :class="['action-button', { saved: isSaved }]"
          @click.stop="toggleSave"
          :disabled="isLoadingSave"
        >
          <img
            :src="isSaved ? '/icons/favorites-white.svg' : '/icons/favorites.svg'"
            alt="Save Icon"
            class="button-icon"
          />
          {{ isSaved ? "Сохранено" : "Сохранить" }}
        </button>
        <button class="action-button">
          <img src="public/icons/Contact.svg" alt="Contact Icon" class="button-icon" />
          <span>Контакт</span>
        </button>
        <button class="action-button" @click.stop="shareEvent">
          <img src="public/icons/Share.svg" alt="Share Icon" class="button-icon" />
          <span>Поделиться</span>
        </button>
        <button class="action-button">
          <img src="public/icons/More.svg" alt="More Icon" class="button-icon" />
          <span>Еще</span>
        </button>
      </div>

      <div class="section">
        <p class="section-title">О событии</p>
        <hr class="divider" />
        <p class="section-content">{{ event.event_desc }}</p>
      </div>
    
      <div v-if="event.favorites_count" class="section">
        <p class="section-title">Статистика</p>
        <hr class="divider" />
        <p class="section-content">{{ Number(event.favorites_count).toLocaleString('ru-RU') }} сохранили</p>
      </div>
    </div>
    
    <div v-else class="loading-container">
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { useWebApp } from "vue-tg";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { usePendingFavorite } from '~/composables/usePendingFavorite';
import { useCardBackground } from '~/composables/useCardBackground';
import "./assets/event-card.css";

definePageMeta({
  layout: "card",
});

interface Event {
  event_id: string;
  event_name: string;
  event_host: string;
  event_date: string;
  event_time: string;
  event_location: string;
  event_banner: string;
  event_desc: string;
  favorites_count: string; 
  events_stats: { uniq_users_likes: number }[];
}

const route = useRoute();
const event = ref<Event | null>(null);
const loadingMessage = ref("Загрузка мероприятия...");

const isSaved = ref(false);
const isLoadingSave = ref(false);
const { initDataUnsafe } = useWebApp();
const pendingAction = usePendingFavorite();

const { dominantColor, gradientBackgroundColor, getAverageColor, gradientBackground } = useCardBackground();

const config = useRuntimeConfig();

const shareEvent = () => {
    if (!event.value) return;
    
    const config = useRuntimeConfig();
    const appBaseUrl = config.public.telegramAppUrl;

    if (!appBaseUrl) {
        console.error("URL приложения не задан в конфигурации!");
        return;
    }

    // 1. Формируем URL, который будет прикреплен к сообщению в виде кнопки-превью.
    const appUrl = `${appBaseUrl}?startapp=event-${event.value.event_id}`;

    // 2. Формируем ТОЛЬКО текст сообщения, БЕЗ ссылки.
    const text = `\nПриходи на "${event.value.event_name}" в приложении Board!`;

    // 3. Создаем URL для шаринга.
    const shareUrl = `https://t.me/share/url?text=${encodeURIComponent(text)}&url=${encodeURIComponent(appUrl)}`;
    
    window.Telegram.WebApp.openTelegramLink(shareUrl);

};





const checkIsFavorite = async (eventId: string) => {
    const userId = initDataUnsafe?.user?.id;
    if (!userId) return;
    try {
        const result = await $fetch<{ isFavorite: boolean }>("/api/isFavorite", {
            method: "POST", body: { user_id: userId, event_id: eventId },
        });
        isSaved.value = result.isFavorite;
    } catch (e) { console.error("Не удалось проверить статус 'избранного'", e); }
};

const toggleSave = () => {
    if (!event.value) return;

    isSaved.value = !isSaved.value;
    if (isSaved.value) {
        if(event.value.favorites_count) {
           event.value.favorites_count = String(Number(event.value.favorites_count) + 1);
        }
    } else {
       if(event.value.favorites_count) {
           event.value.favorites_count = String(Number(event.value.favorites_count) - 1);
        }
    }
  
    pendingAction.value = {
        eventId: event.value.event_id,
        action: isSaved.value ? 'save' : 'unsave',
    };
};

const fetchEvent = async (id: string) => {
    if (!id || id === 'undefined') {
        loadingMessage.value = "Неверный ID мероприятия.";
        return;
    }
    const data = await loadCards(id);
    if (data) {
        if (!data.events_stats) {
            data.events_stats = [{ uniq_users_likes: 0 }];
        }
        event.value = data;
        await nextTick();
        
        if (data.event_banner) {
          dominantColor.value = await getAverageColor(data.event_banner) as { r: number, g: number, b: number };
          gradientBackgroundColor.value = await gradientBackground();
        }

        await checkIsFavorite(id);
        pendingAction.value = { eventId: null, action: null };
    } else {
        loadingMessage.value = "Не удалось загрузить мероприятие.";
    }
};

onMounted(() => {
    fetchEvent(String(route.params.id));
});

const shortWeekdays = { понедельник: "Пн", вторник: "Вт", среда: "Ср", четверг: "Чт", пятница: "Пт", суббота: "Сб", воскресенье: "Вс" };
const capitalizeMonth = (dateStr: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const fullWeekday = format(date, "EEEE", { locale: ru });
    const formattedDate = format(date, "d MMMM", { locale: ru });
    const capitalizedMonth = formattedDate.replace(/\s(\p{L})/u, (match) => match.toUpperCase());
    const shortWeekday = shortWeekdays[fullWeekday.toLowerCase()] || fullWeekday;
    return `${shortWeekday}, ${capitalizedMonth}`;
};
const loadCards = async (id: string) => {
    try {
        const response = await $fetch<{ data?: Event }>("/api/loadCardById", {
            method: "POST", body: { id },
        });
        return response.data || null;
    } catch (err) {
        console.error("Неожиданная ошибка:", err);
        return null;
    }
};
</script>

<style scoped>
.event-page-wrapper {
  position: relative;
  width: 100%;
  min-height: 100vh;
  /* Фон теперь будет динамическим, убираем статичный цвет */
  transition: background 0.5s ease;
  /* Плавный переход фона */
}

.event-page {
  position: relative;
  z-index: 3;
}

.loading-container {
  color: white;
  text-align: center;
  padding-top: 50%;
}

.action-button.saved {
  background-color: #5d5dff;
  color: white;
}

.button-icon {
  width: 22px;
  height: 22px;
  margin-bottom: 4px;
  /* Добавим отступ для текста под иконкой */
}

.action-button {
  flex-direction: column;
  /* Иконка и текст будут друг под другом */
}

.card-image {
  /* Убираем маску, которая создавала "засвет" */
  -webkit-mask-image: none;
  mask-image: none;
}

.event-background {
  /* Этот класс больше не используется для фона, но оставляем на случай, если он нужен для других стилей */
}
</style>