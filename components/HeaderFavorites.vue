<script setup>
import { ref, watch} from 'vue';
import { useRoute, useRouter } from 'vue-router';
import styles from './assets/headerFavorites.module.css';

// Текущая активная вкладка
const activeTab = ref('favorites');
const route = useRoute();
const router = useRouter();

const setActiveTab = (tab) => {
  activeTab.value = tab;
  router.push({ name: tab }); // Переключаем вкладку через роутер
};



// Проверяет, активна ли вкладка
const isActiveTab = (tab) => activeTab.value === tab;


// Следим за изменением роута, чтобы сбрасывать вкладку на "Сохраненные"
watch(
    () => route.path,
    (newPath) => {
      if (newPath === '/favorites') {
        activeTab.value = 'favorites';
      }
    },
    { immediate: true } // Запускаем сразу при монтировании
);


</script>


<template>
  <div :class="styles.header">
    <div :class="styles.tabs">
      <span
          :class="[styles.tab, isActiveTab('favorites') ? styles.activeTab : '']"
          @click="setActiveTab('favorites')"
      >Сохраненные</span>

      <span
          :class="[styles.tab, isActiveTab('my_events') ? styles.activeTab : '']"
          @click="setActiveTab('my_events')"
      >Мои события</span>
    </div>
  </div>
</template>


