<script setup lang="ts">
import { ref } from 'vue';
import CustomSwipe from '~/components/SwipeCard.vue'
import TagSwiper from '~/components/TagSwiper.vue'

// Состояние для фильтрации событий
const filteredEvents = ref<any[]>([]);
const showNoEventsMessage = ref(false);
const noEventsMessage = ref('');
const isLoading = ref(false);

// Обработчики событий от Header компонента
const handleEventsFound = (data: { events: any[], dates: string[], count: number, showAll: boolean }) => {
  console.log('События найдены:', data);
  if (data.showAll) {
    // Если показать все события, очищаем фильтр
    filteredEvents.value = [];
    showNoEventsMessage.value = false;
  } else {
    // Если есть отфильтрованные события
    filteredEvents.value = data.events;
    showNoEventsMessage.value = false;
  }
  isLoading.value = false;
};

const handleNoEventsFound = (data: { message: string, dates: string[] }) => {
  console.log('События не найдены:', data);
  filteredEvents.value = [];
  showNoEventsMessage.value = true;
  noEventsMessage.value = data.message;
  isLoading.value = false;
};

const handleSearchError = (data: { error: any, dates: string[], message: string }) => {
  console.error('Ошибка поиска:', data);
  filteredEvents.value = [];
  showNoEventsMessage.value = true;
  noEventsMessage.value = data.message;
  isLoading.value = false;
};
</script>

<template>
  <section>
    <TagSwiper 
      @events-found="handleEventsFound"
      @no-events-found="handleNoEventsFound"
      @search-error="handleSearchError"
    />
    
    <!-- Сообщение об отсутствии событий -->
    <div v-if="showNoEventsMessage" class="no-events-message">
      <p>{{ noEventsMessage }}</p>
    </div>
    
    <!-- Компонент с карточками событий -->
    <CustomSwipe 
      v-if="!showNoEventsMessage || filteredEvents.length > 0" 
      :filtered-events="filteredEvents"
    />
  </section>
</template>

<style scoped>
.no-events-message {
  color: white;
  text-align: center;
  padding-top: 50%;
}

.no-events-message p {
  margin: 0;
  line-height: 1.5;
  font-size: 16px;
}
</style>