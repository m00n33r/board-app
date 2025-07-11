<script setup>
import { ref, watch} from 'vue';
import { useRoute, useRouter } from 'vue-router';
import styles from './assets/headerFavorites.module.css';

// Определяем, какая вкладка активна, на основе текущего URL
const route = useRoute();
const router = useRouter();
const activeTab = ref(route.name);

// Функция для перехода по маршруту
const setActiveTab = (tabName) => {
  router.push({ name: tabName });
};

// Следим за изменением роута, чтобы обновлять активную вкладку
watch(
    () => route.name,
    (newRouteName) => {
      activeTab.value = newRouteName;
    }
);
</script>

<template>
  <div :class="styles.header">
    <div :class="styles.tabs">
      <span
          :class="[styles.tab, activeTab === 'favorites' ? styles.activeTab : '']"
          @click="setActiveTab('favorites')"
      >
        Сохраненные
      </span>

      <span
          :class="[styles.tab, activeTab === 'myEvents' ? styles.activeTab : '']"
          @click="setActiveTab('myEvents')"
      >
        Мои события
      </span>
    </div>
  </div>
</template>