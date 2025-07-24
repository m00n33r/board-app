<template>
  <div class="swipe-container">
    <div v-if="currentCard" class="card" :style="mergedStyle" @mousedown="startDrag" @touchstart="startDrag"
      @click="goToEvent(currentCard.event_id)">
      <img :src="currentCard.event_banner" alt="Event Banner" class="card-image" />

      <div class="organizer-tag">
        <img src="/icons/user_icon.svg" alt="Organizer" class="organizer-icon" />
        <span>{{ currentCard.event_host }}</span>
      </div>

      <div class="card-info">
        <div class="event-name">{{ currentCard.event_name }}</div>

        <div v-if="currentCard && Number(currentCard.favorites_count) > 0" class="likes-container">
          <div class="event-likes">{{ formattedLikes }} сохранили</div>
        </div>

        <div class="event-desc" v-if="currentCard.event_date">
          {{ currentCard.event_weekday }}, {{ format(parse(currentCard.event_date, 'yyyy-MM-dd', new Date()), "d MMMM",
            { locale: ru }) }},
          {{ currentCard.event_time }} GMT+3
        </div>

        <div class="event-desc">{{ currentCard.event_location }}</div>

        <div class="buttons-container-new">
          <button class="button-new secondary" @click.stop="swipeCard('left')">
            Скип
          </button>
          <button class="button-new secondary" @click.stop="backEvent()"> <img src="/icons/back_button.svg" alt="Назад"
              class="button-icon" />
          </button>
          <button class="button-new secondary" @click.stop="swipeCard('right')">
            Иду
          </button>
        </div>
      </div>
    </div>
    <div v-else class="loading-container">
      <p>Загрузка событий...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import './assets/swiper.css';
import { useWebApp } from "vue-tg";
import { ru } from 'date-fns/locale';
import { useCardBackground } from '~/composables/useCardBackground';
import { useRouter, useRoute } from 'vue-router';
import { format, parse } from 'date-fns';



interface Event {
  event_id: string;
  event_name: string;
  event_time: string;
  event_date: string;
  event_weekday: string;
  event_banner: string;
  event_desc: string;
  event_location: string;
  event_host: string;
  favorites_count: string;
  events_stats: { uniq_users_likes: number }[];
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

const {
  dominantColor,
  gradientBackgroundColor,
  getAverageColor,
  gradientBackground
} = useCardBackground();

const formattedLikes = computed(() => {
  const likes = Number(currentCard.value?.favorites_count) || 0;
  return likes.toLocaleString('ru-RU');
});

const activeStyle = computed(() => ({
  transform: `translateX(${currentX.value}px) rotate(${currentX.value / 10}deg)`,
  transition: isDragging.value ? 'none' : '0.3s',
}));

const mergedStyle = computed(() => ({
  ...activeStyle.value,
  background: gradientBackgroundColor.value
}));

const loadCard = async (eventId: string | null, direction: 'next' | 'prev' | 'current') => {
  try {
    const result = await $fetch<Event | null>('/api/loadCard', {
      method: 'POST',
      body: { eventId, direction }
    });
    return result;
  } catch (err) {
    console.error(`Ошибка загрузки (${direction}):`, err);
    return null;
  }
};

const initCards = async (event_id: string | null) => {
  previousCard.value = null;
  currentCard.value = await loadCard(event_id, event_id ? 'current' : 'next');
  if (currentCard.value) {
    nextCard.value = await loadCard(currentCard.value.event_id, 'next');
  }
};

const swipeCard = async (direction: 'left' | 'right') => {
  if (!currentCard.value) return;

  try {
    const { initDataUnsafe } = useWebApp();
    const user_id = initDataUnsafe?.user?.id;
    if (!user_id) {
      console.error('Ошибка: нет user_id');
      return;
    }

    // Сохраняем "лайк" только при свайпе вправо
    if (direction === 'right') {
      await $fetch<Response>('/api/toggleFavorite', {
        method: 'POST',
        body: {
          user_id,
          event_id: currentCard.value.event_id,
          action: 'save'
        }
      });
    }

    if (nextCard.value) {
      localStorage.setItem('last_event_id', nextCard.value.event_id);
    }
  } catch (err) {
    console.error('Ошибка при свайпе:', err);
  }

  previousCard.value = currentCard.value;
  currentCard.value = nextCard.value;

  if (currentCard.value) {
    nextCard.value = await loadCard(currentCard.value.event_id, 'next');
    if (currentCard.value.event_banner) {
      dominantColor.value = await getAverageColor(currentCard.value.event_banner) as { r: number, g: number, b: number };
      gradientBackgroundColor.value = await gradientBackground();
    }
  }
};

const backEvent = async () => {
  if (!previousCard.value) {
    console.warn("Нет предыдущей карточки");
    return;
  }

  // Меняем карточки местами
  nextCard.value = currentCard.value;
  currentCard.value = previousCard.value;

  if (currentCard.value) {
    // Загружаем новую "предыдущую" карточку
    previousCard.value = await loadCard(currentCard.value.event_id, 'prev');

    if (currentCard.value.event_banner) {
      dominantColor.value = await getAverageColor(currentCard.value.event_banner) as { r: number, g: number, b: number };
      gradientBackgroundColor.value = await gradientBackground();
    }
  }
};


const startDrag = (event: MouseEvent | TouchEvent) => {
  isDragging.value = true;
  startX.value = 'touches' in event ? event.touches[0].clientX : event.clientX;
  document.addEventListener('mousemove', drag);
  document.addEventListener('touchmove', drag);
  document.addEventListener('mouseup', endDrag);
  document.addEventListener('touchend', endDrag);
};

const drag = (event: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return;
  currentX.value = ('touches' in event ? event.touches[0].clientX : event.clientX) - startX.value;
};

const endDrag = () => {
  if (!isDragging.value) return;
  isDragging.value = false;
  if (Math.abs(currentX.value) > 40) {
    swipeCard(currentX.value > 0 ? 'right' : 'left');
  }
  currentX.value = 0;
  document.removeEventListener('mousemove', drag);
  document.removeEventListener('touchmove', drag);
  document.removeEventListener('mouseup', endDrag);
  document.removeEventListener('touchend', endDrag);
};

const route = useRoute();

onMounted(async () => {
  document.body.style.overflow = 'hidden';
  const initialEventId = (route.query.scrollTo as string) || localStorage.getItem('last_event_id');
  await initCards(initialEventId);

  if (currentCard.value) {
    console.log('ПОЛУЧЕННАЯ ДАТА:', currentCard.value.event_date);
  } else {
    console.log('Карточка (currentCard) не загрузилась, проверьте API.');
  }

  if (currentCard.value && currentCard.value.event_banner) {
    dominantColor.value = await getAverageColor(currentCard.value.event_banner) as { r: number, g: number, b: number };
    gradientBackgroundColor.value = await gradientBackground();
  }
});

const router = useRouter();
const goToEvent = (id: string) => {
  if (!id) return;
  router.push(`/event/${id}`);
};

</script>

<style scoped>
.loading-container {
  color: white;
  text-align: center;
  padding-top: 50%;
}


/* 
.button-new.primary {
  background-color: #B3F93F; Яркий акцентный цвет
  color: #1a1a1a; Темный текст для контраста
} */
</style>