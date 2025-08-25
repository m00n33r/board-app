<template>
  <div class="month-container">
    <span class="month">{{ currentMonth }}</span>
  </div>
  <header class="header">
    <div class="dates-container">
      <!-- Отображаем даты с возможностью множественного выбора -->
      <button
          v-for="(date, index) in dates"
          :key="index"
          @click="selectDate(date.day)"
          :class="['date-button', { active: selectedDates.includes(date.day) }]"
      >
        {{ date.day }}
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ru } from 'date-fns/locale';
import { ref, watch } from 'vue';
import { format, addDays } from 'date-fns';

/*
 * Компонент Header с множественным выбором дат
 * 
 * События (emit):
 * - events-found: когда найдены события по выбранным датам
 * - no-events-found: когда в выбранные даты событий нет
 * - search-error: когда произошла ошибка при поиске
 * 
 * Использование в родительском компоненте:
 * <Header 
 *   @events-found="handleEventsFound"
 *   @no-events-found="handleNoEventsFound"
 *   @search-error="handleSearchError"
 * />
 */
const emit = defineEmits(['events-found', 'no-events-found', 'search-error']);

// Получаем текущий месяц
const currentMonth = ref(
    format(new Date(), 'LLLL', { locale: ru }).replace(/^./, (c) => c.toUpperCase())
);

// Функция для проверки, что дата не прошла
const isDateValid = (date: Date): boolean => {
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Сбрасываем время до начала дня
  return date >= today;
};

// Генерация массива дат на ближайшие 30 дней (только будущие)
const dates = ref(
    Array.from({ length: 30 }, (_, i) => {
      const currentDate = addDays(new Date(), i);
      return {
        day: format(currentDate, 'dd', { locale: ru }),
        weekday: format(currentDate, 'EEEE', { locale: ru }),
        iso: format(currentDate, 'yyyy-MM-dd'), // ISO формат для БД
        fullDate: currentDate, // Полная дата для сравнения
      };
    }).filter(date => isDateValid(date.fullDate)) // Фильтруем только будущие даты
);

// Массив для множественного выбора дат
const selectedDates = ref<string[]>([]);

// Функция для выбора/отмены выбора даты
const selectDate = (day: string) => {
  console.log('Клик по дате:', day);
  console.log('Текущие выбранные даты:', selectedDates.value);
  
  const index = selectedDates.value.indexOf(day);
  if (index > -1) {
    // Если дата уже выбрана - убираем её
    selectedDates.value.splice(index, 1);
    console.log('Дата убрана:', day);
  } else {
    // Если дата не выбрана - добавляем её
    selectedDates.value.push(day);
    console.log('Дата добавлена:', day);
  }
  
  console.log('Новые выбранные даты:', selectedDates.value);
};

// Функция для запроса в БД по выбранным датам
const fetchEventsByDates = async () => {
  try {
    // Получаем ISO даты для фильтрации
    const isoDates = dates.value
      .filter(date => selectedDates.value.includes(date.day))
      .map(date => date.iso);
    
    if (selectedDates.value.length === 0) {
      // Если даты не выбраны, загружаем все события
      console.log('Загружаем все события...');
      emit('events-found', {
        events: [],
        dates: [],
        count: 0,
        showAll: true
      });
      return;
    }
    
    console.log('Загружаем события по датам:', isoDates);
    
    // API запрос с фильтром по датам
    const response = await $fetch<{ data?: any[], error?: string }>('/api/loadEventsByDates', {
      method: 'POST',
      body: { dates: isoDates }
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    const events = response.data || [];
    
    if (events.length === 0) {
      // Если событий нет, показываем сообщение
      console.log('В выбранные даты событий нет');
      emit('no-events-found', {
        message: `В выбранные даты (${selectedDates.value.join(', ')}) мероприятий нет :(`,
        dates: selectedDates.value
      });
    } else {
      console.log('Найдено событий:', events.length);
      emit('events-found', {
        events: events,
        dates: selectedDates.value,
        count: events.length,
        showAll: false
      });
    }
  } catch (error) {
    console.error('Ошибка при загрузке событий:', error);
    emit('search-error', {
      error: error,
      dates: selectedDates.value,
      message: 'Произошла ошибка при поиске событий'
    });
  }
};

// Следим за изменением выбранных дат и делаем запрос в БД
watch(selectedDates, () => {
  fetchEventsByDates();
}, { deep: true });
</script>

<style scoped>
.header {
  background-color: #000000;
  color: white;
  padding: 5px 0;
  overflow-x: auto;
  white-space: nowrap;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 2px rgba(0, 0, 0, 0.1);
  z-index: 1;
  flex-direction: column; /* Размещаем элементы вертикально */
}

.dates-container {
  display: flex;
  gap: 0;
  padding: 0 10px;
  width: 95%;
  height: 5vh;
  margin-bottom: 5px;
  overflow-x: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  align-items: center;
}

.dates-container::-webkit-scrollbar { 
  display: none; 
}

.date-button {
  background: none;
  border: none;
  margin: 0;
  cursor: pointer;
  text-align: center;
  flex-shrink: 0;
  min-width: 50px;
  font-size: 17px;
  color: #8e8e93;
  font-weight: normal;
  display: flex;
  align-items: center;
  justify-content: left;
  transition: all 0.3s;
}

.date-button.active {
  color: #B3F93F;
  font-weight: bold;
}

.month-container {
  font-size: 18px;
  text-align: left;
  width: 100%;
  height: 3vh;
  margin-bottom: 0; /* Отступ между месяцем и датами */
  padding-top: 5px;
}

.month {
  font-size: 13px;
  padding: 15px;
  color: #BCBCBC;
  margin-bottom: auto;
}
</style>
