<template>
  <div class="swipe-container">

    <!-- Слайдбар с тегами -->
    <div class="tags-slider-container">
      <div class="tags-slider">
        <div 
          v-for="tag in tags" 
          :key="tag.tag_id"
          class="tag-item"
          :class="{ active: selectedTag === tag.tag_id }"
          @click="selectTag(tag.tag_id)"
        >
          <div class="tag-color" :style="{ backgroundColor: tag.tag_color }"></div>
          <span class="tag-name">{{ tag.tag_name }}</span>
        </div>
      </div>
    </div>

    <div
        v-if="currentCard"
        class="card"
        :style="mergedStyle"
        @mousedown="startDrag"
        @touchstart="startDrag"
        @click="goToEvent(currentCard.event_id)"
    >


      <img :src="currentCard.event_banner" alt="Event Banner" class="card-image" />

      <div class="organizer-tag">
        <img src="/icons/user_icon.svg" alt="Organizer" class="organizer-icon" />
        <span>{{ currentCard.event_host }}</span>
      </div>


      <div class="card-info" >
        <div class="event-name">{{ currentCard.event_name }}</div>


        <div  class="likes-container">
        <div class="event-likes">235 сохранили</div>
        </div>



        <div class="event-desc">{{currentCard.event_weekday}},
          {{format(new Date(currentCard.event_date), "d MMMM", { locale: ru })}}, {{currentCard.event_time}} GMT+3</div>
        <div class="event-desc">{{currentCard.event_location}}</div>



        <div  class="buttons-container">
              <button class="share-button2" @click.stop="shareEvent(currentCard.event_id)">
                <img src="/icons/share_button.svg" alt="Поделиться" />
              </button>


              <button class="share-button2" @click.stop="backEvent()">
                <img src="/icons/back_button.svg" alt="Поделиться" />
              </button>

        </div>

      </div>


    </div>
  </div>
</template>

<script setup lang="ts">


import { ref, computed, onMounted } from 'vue';
import './assets/swiper.css';
import { useTelegram } from '~/composables/useTelegram';
import { v5 as uuidv5 } from 'uuid';

import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useCardBackground } from '~/composables/useCardBackground'


import { useRouter } from 'vue-router';


interface Event {
  event_id: number;
  event_name: string;
  event_time: string;
  event_date: string;
  event_weekday: string;
  event_banner: string;
  event_desc: string;
  event_location: string;
  event_host: string;
  event_tag?: string;
}

interface Tag {
  tag_id: number;
  tag_name: string;
  tag_color: string;
}

interface Response {
  success?: boolean
  error?: string
}

const startX = ref(0);
const currentX = ref(0);
const isDragging = ref(false);

const currentCard = ref<Event | null>(null);
const nextCard = ref<Event | null>(null);
const previousCard = ref<Event | null>(null);

// Теги
const tags = ref<Tag[]>([]);
const selectedTag = ref<number | null>(null);

// Используем наш composable для Telegram
const { user, isReady, error: telegramError } = useTelegram();

const {
  dominantColor,
  gradientBackgroundColor,
  getAverageColor,
  gradientBackground
} = useCardBackground()


// Стили активной карточки
const activeStyle = computed(() => ({
  transform: `translateX(${currentX.value}px) rotate(${currentX.value / 10}deg)`,
  transition: isDragging.value ? 'none' : '0.3s',
}));

const mergedStyle = computed(() => ({
  ...activeStyle.value,
  background: gradientBackgroundColor.value
}));

// Загрузка тегов
const loadTags = async () => {
  try {
    const result = await $fetch('/api/tags', {
      method: 'GET'
    })
    tags.value = result || []
  } catch (err) {
    console.error('Ошибка загрузки тегов:', err)
  }
}

// Выбор тега
const selectTag = (tagId: number) => {
  selectedTag.value = selectedTag.value === tagId ? null : tagId;
  // Перезагружаем карточки с учетом выбранного тега
  if (currentCard.value) {
    initCards(currentCard.value.event_id);
  }
}

const loadCard = async (eventId: number | null, direction: 'next' | 'prev' | 'current') => {
  try {
    const result = await $fetch('/api/loadCard', {
      method: 'POST',
      body: {
        eventId,
        direction,
        tagId: selectedTag.value
      }
    })

    return result
  } catch (err) {
    console.error(`Ошибка загрузки (${direction}):`, err)
    return null
  }
}

const initCards = async (event_id) => {



  previousCard.value = null;

  if (event_id) {
    currentCard.value = await loadCard(event_id, 'current');
  } else {
    currentCard.value = await loadCard(null, 'next');
  }

  if (currentCard.value) {
    nextCard.value = await loadCard(currentCard.value.event_id, 'next');
  }

};




const swipeCard = async (direction: 'left' | 'right') => {
  if (!currentCard.value) return

  try {
    // Используем user_id из нашего composable
    let user_id = null;
    
    if (user.value?.id) {
      user_id = user.value.id.toString();
    } else if (telegramError.value) {
      console.error('Ошибка Telegram:', telegramError.value);
      // Пробуем получить из localStorage как fallback
      user_id = localStorage.getItem('user_id');
    }

    if (!user_id) {
      console.error('Ошибка: нет user_id')
      return
    }

    // Отправка свайпа на сервер
    const response = await $fetch<Response>('/api/swapEvent', {
      method: 'POST',
      body: {
        user_id,
        event_id: currentCard.value.event_id,
        direction
      }
    })

    if (response.error) {
      console.error('Ошибка при свайпе:', response.error)
    } else {
      console.log('Свайп сохранён')

      await recalculateFavorites(user_id)
      localStorage.setItem('last_event_id', nextCard.value.event_id.toString())
    }
  } catch (err) {
    console.error('Ошибка отправки запроса:', err)
  }

  // Переключаем карточки
  previousCard.value = currentCard.value
  currentCard.value = nextCard.value
  nextCard.value = await loadCard(currentCard.value?.event_id || null, 'next')

  dominantColor.value = await getAverageColor(currentCard.value.event_banner) as { r: number, g: number, b: number };
  gradientBackgroundColor.value = await gradientBackground();
}



const backEvent = async () => {
  if (!previousCard.value) {
    console.warn("Нет предыдущей карточки");
    return;
  }


  nextCard.value = currentCard.value;
  currentCard.value = previousCard.value;
  previousCard.value = await loadCard(previousCard.value.event_id, 'prev');


};

// Начало перетаскивания
const startDrag = (event) => {
  isDragging.value = true;
  startX.value = event.touches ? event.touches[0].clientX : event.clientX;
  document.addEventListener('mousemove', drag);
  document.addEventListener('touchmove', drag);
  document.addEventListener('mouseup', endDrag);
  document.addEventListener('touchend', endDrag);
};

// Перетаскивание
const drag = (event) => {
  if (!isDragging.value) return;
  currentX.value =
      (event.touches ? event.touches[0].clientX : event.clientX) - startX.value;
};


// Завершение перетаскивания
const endDrag = () => {
  if (!isDragging.value) return;

  isDragging.value = false;

  // Проверяем, был ли свайп достаточно длинным
  if (Math.abs(currentX.value) > 40) {
    swipeCard(currentX.value > 0 ? 'right' : 'left');
  }

  // Сбрасываем положение текущей карточки
  currentX.value = 0;

  // Удаляем слушатели
  document.removeEventListener('mousemove', drag);
  document.removeEventListener('touchmove', drag);
  document.removeEventListener('mouseup', endDrag);
  document.removeEventListener('touchend', endDrag);
};


const generateUniqueId = (user_id, event_id, timestamp) => {
  const namespace = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'; // Уникальный namespace
  const data = `${user_id}_${event_id}_${timestamp}`;
  return uuidv5(data, namespace);
};

const route = useRoute();

// Загружаем карточки при монтировании компонента
onMounted(async () => {


  // Отключаем скролл
  document.body.style.overflow = 'hidden';

  // Загружаем теги
  await loadTags();

  // Ждем готовности Telegram
  if (!isReady.value) {
    await new Promise(resolve => {
      const checkReady = () => {
        if (isReady.value) {
          resolve(true);
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    });
  }

  // Сохраняем user_id в localStorage для fallback
  if (user.value?.id) {
    localStorage.setItem('user_id', user.value.id.toString());
  }

  // последняя карточка, которую видел пользователь
  const savedEventId = localStorage.getItem('last_event_id');


  if (route.query.scrollTo) {
    await initCards(route.query.scrollTo)
  } else {
    await initCards(parseInt(savedEventId));
  }


  dominantColor.value = await getAverageColor(currentCard.value.event_banner) as { r: number, g: number, b: number };
  gradientBackgroundColor.value = await gradientBackground();


});


const shareEvent = (card) => {
  const eventUrl = `@board_mini_app_bot`;
  const text =  ``;
  // const text = `Посмотри это мероприятие: ${card.event_name}`;

  // Ссылка для открытия Telegram
  const telegramShareUrl = `https://t.me/share/url?url=${encodeURIComponent(eventUrl)}&text=${encodeURIComponent(text)}`;

  // Открыть Telegram с указанной ссылкой
  window.open(telegramShareUrl, '_blank');
};


const router = useRouter();
const goToEvent = (id: number) => {
  router.push(`/event/${id}`);
};



// При клике свайпе вправо/влево надо добавлять или удалять favorites
const recalculateFavorites = async (userId: string) => {
  try {
    const response = await $fetch<Response>('/api/recalculateFavorites', {
      method: 'POST',
      body: {
        user_id: userId
      }
    })

    if (response.error) {
      console.error('Ошибка пересчёта избранного:', response.error)
    } else {
      console.log('Избранное пересчитано успешно!')
    }
  } catch (err) {
    console.error('Ошибка при запросе пересчёта избранного:', err)
  }
}



</script>

<style scoped>
.tags-slider-container {
  position: fixed;
  top: 20px;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: 0 20px;
}

.tags-slider {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 8px 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.tags-slider::-webkit-scrollbar {
  display: none;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.tag-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.tag-item.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .tags-slider-container {
    top: 10px;
    padding: 0 10px;
  }
  
  .tag-item {
    padding: 6px 12px;
  }
  
  .tag-name {
    font-size: 12px;
  }
}
</style>
