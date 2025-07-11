<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";
// 1. Импортируем onActivated
import { onMounted, onActivated, ref } from "vue";
import { useWebApp } from "vue-tg";
import styles from './assets/favorites.module.css';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

definePageMeta({
  layout: 'header-favorites',
});

interface Event {
  event_name: string;
  event_id: string;
  event_banner: string;
  event_host: string;
  event_date: string;
  event_time: string;
  event_location: string;
}

const favorite_events = ref<Event[]>([]);
const router = useRouter();
const route = useRoute();

const goToEvent = (id: string) => {
  router.push({
    path: `/event/${id}`,
    query: { from: route.fullPath },
  });
};

interface LoadFavoritesResponse {
  data?: Event[]
  error?: string
}

const loadFavorites = async (userId) => {
  try {
    const response = await $fetch<LoadFavoritesResponse>('/api/loadFavorites', {
      method: 'POST',
      body: { user_id: userId }
    });

    if (response.error) {
      console.error('Ошибка при загрузке избранного:', response.error);
      return;
    }

    favorite_events.value = response.data || [];
  } catch (err) {
    console.error('Ошибка запроса избранного:', err);
  }
};

// 2. Создаем единую функцию для загрузки данных
const loadData = () => {
    const { initDataUnsafe } = useWebApp();
    const userId = initDataUnsafe?.user?.id;

    if (userId) {
        loadFavorites(userId);
    }
}

// 3. Вызываем загрузку данных при первой загрузке
onMounted(loadData);

// 4. Вызываем загрузку данных при каждом возвращении на страницу
onActivated(loadData);


const shortWeekdays = {
  понедельник: "Пн",
  вторник: "Вт",
  среда: "Ср",
  четверг: "Чт",
  пятница: "Пт",
  суббота: "Сб",
  воскресенье: "Вс",
};

const capitalizeMonth = (dateStr: string) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const fullWeekday = format(date, "EEEE", { locale: ru });
  const formattedDate = format(date, "d MMMM", { locale: ru });
  const capitalizedMonth = formattedDate.replace(/\s(\p{L})/u, (match) => match.toUpperCase());
  const shortWeekday = shortWeekdays[fullWeekday.toLowerCase()] || fullWeekday;
  return `${shortWeekday}, ${capitalizedMonth}`;
};
</script>

<template>
  <div :class="styles.saved_events_page">
    <div :class="styles.events_container">
      <div
          v-if="favorite_events.length > 0"
          :class="styles.event_card"
          v-for="(event, index) in favorite_events"
          :key="index"
          @click="goToEvent(event.event_id)">

        <div :class="styles.event_image">
          <img v-if="event.event_banner" :src="event.event_banner" alt="Event Banner" />
        </div>

        <div :class="styles.event_details">
          <h3 :class="styles.event_name">{{event.event_name}}</h3>
          <p :class="styles.event_host">@{{event.event_host}}</p>
          <div :class="styles.event_meta">
            <div :class="styles.event_date">
              <span :class="styles.icon"><img src="/icons/Date.svg" /></span>
              <span :class="styles.icon">{{ capitalizeMonth(event.event_date) }}</span>
              <span :class="styles.icon" style="margin-left: 8px;"><img src="/icons/Time.svg" /></span>
              <span>{{event.event_time}} GMT+3</span>
            </div>
            <div :class="styles.event_location">
              <span :class="styles.icon"><img src="/icons/Location.svg" /></span>
              <span>{{event.event_location}}</span>
            </div>
            <div :class="styles.event_separator"></div>
          </div>
        </div>
      </div>
       <div v-else>
        <p>У вас пока нет сохраненных мероприятий.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow-x: hidden;
}
p {
  color: var(--tg-theme-hint-color);
  text-align: center;
  margin-top: 20px;
}
</style>