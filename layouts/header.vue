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
  overflow: hidden; /* Telegram лучше работает с отключённой прокруткой на уровне документа */
}

.main-content {
  flex: 1; /* Растягиваем контентный блок */
  overflow-y: auto; /* Прокрутка активна только для основного контента */
  padding-bottom: 87px; /* Отступ снизу под футер */
}



</style>