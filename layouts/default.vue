<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import './assets/styles.css';
import { useWebApp } from 'vue-tg'; 

//
// --- ВАЖНО: ВЫЗЫВАЕМ ФУНКЦИЮ useWebApp() ЗДЕСЬ ---
//
const { initDataUnsafe } = useWebApp();

const isUserChecked = ref(false);

const checkAndAddUser = async (data: any) => {
  try {
    const userId = data?.user?.id;
    // ... остальной код функции без изменений
    const userFirstName = data?.user?.first_name;
    const userLastName = data?.user?.last_name;
    const userName = data?.user?.username;
    const userCreatedDate = new Date().toISOString().split('T')[0];

    await fetch('/api/users/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        userFirstName,
        userLastName,
        userName,
        userCreatedDate
      }),
    });
    isUserChecked.value = true;
  } catch (error) {
    console.error('Ошибка при проверке пользователя:', error);
  }
};

onMounted(() => {
  document.documentElement.style.overflow = 'hidden';
  document.body.style.overflow = 'hidden';
  
  // Здесь мы просто используем уже готовые данные
  const userId = initDataUnsafe?.user?.id;

  if (userId) {
    // Передаем initDataUnsafe, а не вызываем useWebApp() заново
    checkAndAddUser(initDataUnsafe);
  } else {
    console.error('User ID не передан Telegram');
  }
});

onBeforeUnmount(() => {
  document.documentElement.style.overflow = '';
  document.body.style.overflow = '';
});
</script>

<template>
  <div>
    <main class="main-content">
      <NuxtPage />
    </main>
    <Footer />
  </div>
</template>

<style scoped>
</style>