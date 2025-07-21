<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue';
import { useWebApp } from 'vue-tg';
import { useRouter } from 'vue-router';

const { initDataUnsafe, ready } = useWebApp();
const router = useRouter();

onMounted(() => {
  // Инициализируем приложение Telegram
  window.Telegram.WebApp.disableVerticalSwipes();
  window.Telegram.WebApp.setBackgroundColor("#000000");
  ready();


  // Обработка глубоких ссылок
  const startParam = initDataUnsafe?.start_param;
  if (startParam && startParam.startsWith('event-')) {
    const eventId = startParam.split('event-')[1];
    if (eventId) {
      router.push(`/event/${eventId}`);
    }
  }
});
</script>

<style>
html,
body {
  background-color: #000;
  font-family: 'Inter', sans-serif !important;
}
</style>