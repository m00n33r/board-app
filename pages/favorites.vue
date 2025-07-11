<script setup lang="ts">


definePageMeta({
  layout: 'header-favorites',
});


import {useRouter} from "#vue-router";
import styles from './assets/favorites.module.css';
import {onMounted, ref} from "vue";
import {useWebApp} from "vue-tg";
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

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

// Загружаем карточки при монтировании компонента
onMounted(() => {

  console.log(getComputedStyle(document.body).fontFamily);

  const {initDataUnsafe} = useWebApp();
  const userId = initDataUnsafe?.user?.id;

  loadFavorites(userId);


});

const route = useRoute();
const router = useRouter();

const goToEvent = (id: string) => {

  router.push({
        path: `/event/${id}`,
        query: { from: route.fullPath },
      }
  );
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
    })

    if (response.error) {
      console.error('Ошибка при загрузке избранного:', response.error)
      return
    }

    favorite_events.value = response.data || []
  } catch (err) {
    console.error('Ошибка запроса избранного:', err)
  }
};


// Список сокращённых дней недели
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
  const date = new Date(dateStr);

  // Получаем полное название дня недели и месяца
  const fullWeekday = format(date, "EEEE", { locale: ru }); // "понедельник"
  const formattedDate = format(date, "d MMMM", { locale: ru }); // "1 января"

  // Делаем первую букву месяца заглавной
  const capitalizedMonth = formattedDate.replace(/\s(\p{L})/u, (match) => match.toUpperCase());

  // Получаем сокращённый день недели
  const shortWeekday = shortWeekdays[fullWeekday.toLowerCase()] || fullWeekday;

  return `${shortWeekday}, ${capitalizedMonth}`;
};




</script>

<template>
  <div :class="styles.saved_events_page">
    <div :class="styles.events_container">
      <div
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
              <span :class="styles.icon">
                <img src="/icons/Date.svg" />
              </span>
              <span :class="styles.icon">
                {{ capitalizeMonth(event.event_date) }}
              </span>
              <span :class="styles.icon">
                <img src="/icons/Time.svg" />
              </span>
              <span>{{event.event_time}} GMT+3</span>
            </div>
            <div :class="styles.event_location">
              <span :class="styles.icon">
                <img src="/icons/Location.svg" />
              </span>
              <span>{{event.event_location}}</span>
            </div>
            <div :class="styles.event_separator"></div>
          </div>
        </div>
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



</style>


