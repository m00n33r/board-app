<template>
  <div class="swiper-container">
    <!-- Header с выбором дат -->
    <Header 
      @events-found="handleEventsFound"
      @no-events-found="handleNoEventsFound"
      @search-error="handleSearchError"
    />
    
    <!-- Теги -->
    <div class="tags-container">
      <button
        @click="handleTagClick('Все')"
        :class="['tag-button', 'all-button', { active: activeTags.length === 0 }]"
      >
        Все
      </button>
      
      <div v-if="tagsPending">Загрузка тегов...</div>
      <div v-else-if="tagsError">Ошибка загрузки</div>

      <button
        v-else
        v-for="tag in availableTags"
        :key="tag.tag_name"
        @click="handleTagClick(tag.tag_name)"
        :class="['tag-button', { active: activeTags.includes(tag.tag_name) }]"
        :style="{ 
          backgroundColor: activeTags.includes(tag.tag_name) ? tag.tag_color : '#ffffff'
        }"
      >
        {{ tag.tag_name }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import Header from './Header.vue';

interface Tag {
  tag_name: string;
  tag_color: string;
}

// Обработчики событий от Header компонента
const emit = defineEmits(['events-found', 'no-events-found', 'search-error']);

const handleEventsFound = (data: { events: any[], dates: string[], count: number, showAll: boolean }) => {
  emit('events-found', data);
};

const handleNoEventsFound = (data: { message: string, dates: string[] }) => {
  emit('no-events-found', data);
};

const handleSearchError = (data: { error: any, dates: string[], message: string }) => {
  emit('search-error', data);
};

const activeTags = ref<string[]>([]);
const availableTags = ref<Tag[]>([]);
const tagsPending = ref(false);
const tagsError = ref<Error | null>(null);

// Загружаем теги из БД
const loadTags = async () => {
  tagsPending.value = true;
  try {
    const tags = await $fetch<Tag[]>('/api/tagsGet');
    availableTags.value = tags;
  } catch (err) {
    console.error('Ошибка загрузки тегов:', err);
    tagsError.value = err as Error;
  } finally {
    tagsPending.value = false;
  }
};

const handleTagClick = (tagName: string) => {
  if (tagName === 'Все') {
    activeTags.value = [];
    return;
  }
  const index = activeTags.value.indexOf(tagName);
  if (index > -1) {
    activeTags.value.splice(index, 1);
  } else {
    activeTags.value.push(tagName);
  }
};

onMounted(() => {
  loadTags();
});
</script>

<style scoped>
.swiper-container {
  width: 100%;
}

.tags-container {
  display: flex;
  overflow-x: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  padding: 0px 0px 10px 15px;
  min-height: 32px;
  align-items: center;
  margin-top: 0px;
}

.tags-container::-webkit-scrollbar { 
  display: none; 
}

.tag-button {
  display: flex;
  align-items: center;
  color: #000; 
  padding: 6px 12px;
  margin-right: 6px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
  white-space: nowrap;
  font-weight: 700;
  background-color: #f2f2f7;
  font-size: 14px;
  border: none;
}

.tag-button.active {
  color: #000;
  border: none;
}

.tags-container .tag-button:first-child {
  background-color: #f2f2f7;
  color: #000;
  border: none;
}

.tags-container .tag-button:first-child.active {
    background-color: #f2f2f7;
  color: #000;
  border: none;
}
</style>
