<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";
import { onMounted, onActivated, ref, watch } from "vue";
import { useWebApp } from "vue-tg";
import styles from './assets/favorites.module.css'

definePageMeta({
  layout: 'header-favorites',
});

interface Event {
  event_id: string;
  event_name: string;
  event_banner: string;
  event_host: string;
  event_start_dttm: string;
  event_location: string;
  event_moderation_step: string;
}

const myEvents = ref<Event[]>([]);
const isLoading = ref(true);
const showNotification = ref(false);
const router = useRouter();
const route = useRoute();

const triggerNotification = () => {
  showNotification.value = true;
  setTimeout(() => showNotification.value = false, 3000);
};

const formatDate = (datetime: string) => {
  if (!datetime) return { date: '', time: '' };
  const d = new Date(datetime);
  const date = d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long' });
  const time = d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  return { date, time };
};

const loadMyEvents = async (userId: number) => {
  isLoading.value = true;
  myEvents.value = [];
  try {
    const response = await $fetch<{ data?: Event[], error?: string }>('/api/loadMyEvents', {
      method: 'POST',
      body: { user_id: userId }
    });

    if (response.error) {
      console.error('Ошибка при загрузке мероприятий:', response.error);
    } else {
      myEvents.value = (response.data || []).sort((a, b) => new Date(b.event_start_dttm).getTime() - new Date(a.event_start_dttm).getTime());
    }
  } catch (err) {
    console.error('Ошибка запроса мероприятий:', err);
  } finally {
    isLoading.value = false;
  }
};

const loadData = () => {
  const { initDataUnsafe } = useWebApp();
  const userId = initDataUnsafe?.user?.id;
  if (userId) {
    loadMyEvents(userId);
  } else {
    isLoading.value = false;
  }
};

watch(() => route.query, (newQuery) => {
    if (newQuery.created === 'true') {
      triggerNotification();
      const { created, ...queryWithoutCreated } = newQuery;
      router.replace({ query: queryWithoutCreated });
    }
  },
  { immediate: true }
);

onMounted(loadData);
onActivated(loadData);

const goToEvent = (id: string) => {
  router.push({
    path: `/event/${id}`,
    query: { from: route.fullPath },
  });
};
</script>

<template>
  <div>
    <div v-if="showNotification" class="notification-popup">
      Мероприятие отправлено на модерацию!
    </div>
    
    <div :class="styles.saved_events_page">
      <div :class="styles.events_container">

        <div v-if="isLoading">
          <p>Загрузка мероприятий...</p>
        </div>
        <div v-else-if="myEvents.length > 0">
          <div
            :class="styles.event_card"
            v-for="event in myEvents"
            :key="event.event_id"
            @click="goToEvent(event.event_id)">
            
            <div :class="styles.event_image">
              <img v-if="event.event_banner" :src="event.event_banner" alt="Event Banner" />
            </div>

            <div :class="styles.event_details">
              <h3 :class="styles.event_name">{{ event.event_name }}</h3>
              <p v-if="event.event_host" :class="styles.event_host">By @{{ event.event_host }}</p>
              <div :class="styles.event_meta">
                <div :class="styles.event_date">
                  <span :class="styles.icon"><img src="/icons/Date.svg" /></span>
                  <span>{{ formatDate(event.event_start_dttm).date }}</span>
                  <span :class="styles.icon" style="margin-left: 8px;"><img src="/icons/Time.svg" /></span>
                  <span>{{ formatDate(event.event_start_dttm).time }}</span>
                </div>
                <div :class="styles.event_location">
                  <span :class="styles.icon"><img src="/icons/Location.svg" /></span>
                  <span>{{ event.event_location }}</span>
                </div>
                <div v-if="event.event_moderation_step === 'На модерации'" class="moderation_status">
                  {{ event.event_moderation_step }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else>
          <p>У вас пока нет созданных мероприятий.</p>
        </div>

      </div>
    </div>
  </div>
</template>


<style scoped>
.moderation_status {
  background-color: #ffc107;
  color: #000;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 5px;
  display: inline-block;
}

.notification-popup {
  position: fixed;
  top: 60px; /* Располагаем под хедером */
  left: 50%;
  transform: translateX(-50%);
  background-color: #4CAF50; /* Зеленый цвет успеха */
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  z-index: 10000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  transition: opacity 0.5s, top 0.5s;
}
</style>