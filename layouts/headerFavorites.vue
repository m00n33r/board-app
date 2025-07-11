<script setup lang="ts">

import { onMounted} from 'vue';

onMounted(() => {
 if (window.Telegram?.WebApp) {
    Telegram.WebApp.expand(); // Расширяет приложение


  }

});

</script>

<template>



    <HeaderFavorites/>

    <main>


      <NuxtPage />

    </main>

    <Footer />


</template>

<style scoped>

html, body {
  height: 100%;
  margin: 0;
  overflow: hidden; /* Telegram лучше работает с отключённой прокруткой на уровне документа */
}


</style>