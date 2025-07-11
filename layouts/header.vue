<script setup lang="ts">
import { onMounted } from 'vue';

onMounted(() => {
  if (window.Telegram?.WebApp) {
    Telegram.WebApp.expand(); // Расширяет приложение
  }
});
</script>

<template>
  <div>
    <main class="main-content">
      <NuxtPage />
    </main>
    <Footer class="footer"/>
  </div>
</template>

<style scoped>
html, body {
  height: 100%;
  margin: 0;
  overflow: hidden;
}

.main-content {
  /* Растягиваем контентный блок */
  flex: 1;
  /* Включаем вертикальную прокрутку */
  overflow-y: auto;
  /* ДОБАВЛЯЕМ ОТСТУП, РАВНЫЙ ВЫСОТЕ ФУТЕРА */
  padding-bottom: 87px;
  /* Высота контейнера, чтобы он занимал все доступное место */
  height: 100vh;
  box-sizing: border-box; /* Чтобы padding не увеличивал высоту */
}
</style>