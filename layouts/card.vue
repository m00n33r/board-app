<template>
  <div>
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { usePendingFavorite } from '~/composables/usePendingFavorite';
import { useWebApp } from "vue-tg";
import { useRouter } from 'vue-router'; 

interface TelegramWebApp {
  WebApp: {
    BackButton: {
      show: () => void;
      hide: () => void;
      onClick: (callback: () => void) => void;
      offClick: (callback: () => void) => void;
    };
    close: () => void;
  };
}

const router = useRouter(); 
const pendingAction = usePendingFavorite();
const { initDataUnsafe } = useWebApp();

const handleBackClick = async () => {
  if (pendingAction.value && pendingAction.value.eventId && pendingAction.value.action) {
    const userId = initDataUnsafe?.user?.id;
    if (userId) {
      const payload = {
        user_id: userId,
        event_id: pendingAction.value.eventId,
        action: pendingAction.value.action,
      };
      
      $fetch('/api/toggleFavorite', {
        method: 'POST',
        body: payload
      }).catch(err => {
        console.error("Ошибка отложенного сохранения:", err.data || err);
      });
    }
    pendingAction.value = { eventId: null, action: null };
  }

  // Проверяем, есть ли куда возвращаться в истории
  if (window.history.state.back) {
    router.back();
  } else {
    // Если истории нет (пришли по прямой ссылке), переходим на главную
    router.push('/');
  }
};

onMounted(() => {
  if (process.client && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.BackButton.show();
    tg.BackButton.onClick(handleBackClick);
  }
});

onUnmounted(() => {
  if (process.client && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.BackButton.offClick(handleBackClick);
    tg.BackButton.hide();
  }
});
</script>

<style scoped></style>