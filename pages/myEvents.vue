<script setup lang="ts">


import {useRouter} from "#vue-router";
import {onMounted, ref} from "vue";
import {useWebApp} from "vue-tg";
import styles from './assets/favorites.module.css'

definePageMeta({
  layout: 'header-favorites',
});



interface Event {
  event_name: string;
  event_id: string;
  event_banner: string;
  event_host: string;
  event_date: string;
  event_time: string;
  event_location: string;



}

const favorite_events = ref<Event[]>([]);


// Загружаем карточки при монтировании компонента
onMounted(() => {

  console.log(getComputedStyle(document.body).fontFamily);

  const {initDataUnsafe} = useWebApp();
  const userId = initDataUnsafe?.user?.id;


  // recalculateFavorites(userId);
  // loadFavorites.ts(userId);


});

const route = useRoute();
const router = useRouter();

const goToEvent = (id: string) => {

  router.push({
        path: `/event/${id}`,
        query: { from: route.fullPath },
      }
  );
};


</script>

<template>
  <div :class="styles.saved_events_page">
    <div :class="styles.events_container">
      <div
          :class="styles.event_card"
          v-for="(event, index) in favorite_events"
          :key="index"
          @click="goToEvent(event.event_id)">

        <div :class="styles.event_image">
          <img v-if="event.event_banner" :src="event.event_banner" alt="Event Banner" />
        </div>

        <div :class="styles.event_details">

          <h3 :class="styles.event_name">{{event.event_name}}</h3>
          <p :class="styles.event_host">By @{{event.event_host}}</p>
          <div :class="styles.event_meta">
            <div :class="styles.event_date">
              <span :class="styles.icon">
                <img src="/icons/Date.svg" />
              </span>
              <span :class="styles.icon">{{event.event_date}} </span>
              <span :class="styles.icon">
                <img src="/icons/Time.svg" />
              </span>
              <span>{{event.event_time}}</span>
            </div>
            <div :class="styles.event_location">
              <span :class="styles.icon">
                <img src="/icons/Location.svg" />
              </span>
              <span>{{event.event_location}}</span>
            </div>
            <div :class="styles.event_separator"></div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow-x: hidden;
}



</style>


