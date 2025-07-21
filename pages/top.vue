<script setup lang="ts">



import {useRouter} from "#vue-router";

definePageMeta({
  layout: 'header',
});


import styles from './assets/top.module.css'
import {onMounted, ref} from "vue";
import {useWebApp} from "vue-tg";
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

interface topEvent {

  event_id: string;
  event_name: string;
  event_host: string;
  event_date: string;
  event_time: string;
  event_location: string;
  event_banner: string;

}

const top_events = ref<topEvent[]>([]);
const router = useRouter();
const route = useRoute();

onMounted(() => {


  top_events.value = []


  const {initDataUnsafe} = useWebApp();
  const userId = initDataUnsafe?.user?.id;


  loadTopEvents(userId);

});


interface LoadTopEventsResponse {
  data?: topEvent[]
  source?: string
  error?: string
}

const loadTopEvents = async (userId: string) => {
  try {
    const response = await $fetch<LoadTopEventsResponse>('/api/loadTopEvents', {
      method: 'POST',
      body: { user_id: userId }
    })

    if (response.error) {
      console.error('Ошибка загрузки топ-событий:', response.error)
      return
    }

    top_events.value = response.data || []

    console.log(`События получены из: ${response.source}`)
  } catch (err) {
    console.error('Ошибка запроса топ-событий:', err)
  }
}


const getTrophyIcon = (index: number) => {
  const trophyIcons = ["/icons/gold.svg", "/icons/silver.svg", "/icons/bronze.svg"];
  return trophyIcons[index];
};


const goToEvent = (id: string) => {
  if (!id) return;
  router.push(`/event/${id}`);
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

  <div :class="styles.fixed_header">
    <div :class="styles.page_title">Топ событий Москвы</div>
  </div>



  <div :class="styles.top_events_page">
    <div :class="styles.event_list">
      <div
          :class="styles.event_card"
          v-for="(event, index) in top_events"
          :key="index"
          @click="goToEvent(event.event_id)"
      >
        <div :class="styles.rank_icon">
          <img
              v-if="index < 3"
              :src="getTrophyIcon(index)"
              alt="Rank Trophy"
          />

          <span v-else>{{ index + 1 }}</span>
        </div>


        <div :class="styles.event_banner2">
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



</style>