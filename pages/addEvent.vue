<script setup lang="ts">

definePageMeta({
  layout: 'header',
});

interface Response {
  success?: boolean
  error?: string
}

interface UploadImageResponse {
  url?: string
  error?: string
}

import { ref } from "vue";
import styles from "./assets/event_create.module.css"; // Подключаем модульные стили


const eventStart = ref("");
const eventEnd = ref("");



// Функция для вычисления ближайшего часа
const getNearestHourMoscow = () => {
  // Текущее время в Москве (UTC+3)
  const now = new Date(new Date().toLocaleString("en-US", { timeZone: "Europe/Moscow" }));

  now.setMinutes(0, 0, 0); // Обнуляем минуты и секунды
  now.setHours(now.getHours() + 1); // Прибавляем 1 час

  // Преобразуем в формат для input[type="datetime-local"]
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0"); // Месяцы с 0
  const day = String(now.getDate()).padStart(2, "0");
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = "00"; // Всегда ставим ровный час

  return `${year}-${month}-${day}T${hours}:${minutes}`;
};


const eventDesc = ref("");
const tempDesc = ref("");
const showDescModal = ref(false);

// Закрытие окна описания
const closeDescModal = () => {
  showDescModal.value = false;
  document.body.style.overflow = "";
};

// Сохранение описания
const saveDescription = () => {
  eventDesc.value = tempDesc.value.trim();
  closeDescModal();
};


// Функция загрузки изображения
const uploadImage = async (event) => {


  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await $fetch<UploadImageResponse>('/api/uploadImage', {
      method: 'POST',
      body: formData
    })

    if (response.error) {
      alert('Ошибка загрузки файла')
      console.error('Ошибка:', response.error)
      return
    }

    eventBanner.value = response.url
  } catch (err) {
    alert('Ошибка при отправке запроса')
    console.error(err)
  }


};




// Поля формы
const eventBanner = ref(null);




const eventName = ref("");
const eventPrice = ref("");
const eventApproval = ref(false);
const eventLinks = ref("");
const eventTags = ref("");
const eventLocation = ref("");
const eventPriceStatus = ref("Бесплатно");
const eventVisibility = ref("Публичное");
const eventCapacity = ref("Limited");


const closeKeyboard = (event: Event) => {

  const target = event.target as HTMLElement;

  if (target.closest("select")) return;

  // Если клик НЕ по инпуту и НЕ по текстовой области, убираем фокус
  if (target && !target.closest("input, textarea")) {
    document.activeElement?.blur();
  }
};

onMounted(() => {

  document.addEventListener("click", closeKeyboard);
  eventStart.value = getNearestHourMoscow();
  eventEnd.value = getNearestHourMoscow();


});

onUnmounted(() => {
  document.removeEventListener("click", closeKeyboard);
});


const isFormValid = computed(() => {

  if (eventPriceStatus.value == 'Бесплатно'){
    return eventName.value &&
        eventStart.value &&
        eventEnd.value &&
        eventLocation.value &&
        eventDesc.value &&
        eventTags.value &&
        eventLinks.value &&
        eventBanner.value;
  }

  return eventName.value &&
        eventStart.value &&
        eventEnd.value &&
        eventLocation.value &&
        eventDesc.value &&
        eventTags.value &&
        eventLinks.value &&
        eventBanner.value &&
        eventPrice.value;
});


const createEvent = async () => {


  if (!isFormValid.value) {
    return;
  }

  const response = await $fetch<Response>('/api/createEvent', {
    method: 'POST',
    body: {
      event_name: eventName.value,
      event_banner: eventBanner.value,
      event_start_dttm: eventStart.value,
      event_end_dttm: eventEnd.value,
      event_location: eventLocation.value,
      event_description: eventDesc.value,
      event_tag: eventTags.value,
      event_link: eventLinks.value,
      event_approval: eventApproval.value,
      event_price_status: eventPriceStatus.value,
      event_price: eventPrice.value,
      event_visibility: eventVisibility.value,
      event_capacity: eventCapacity.value,
    }
  });


  if (response.error) {
    console.error('Ошибка:', response.error);
  } else {
    console.log('Успешное добавление события');
    resetForm();
    alert("Поздравляю! Ваше мероприятие отправлено на модерацию...");
  }

};


const resetForm = () => {
  eventName.value = "";
  eventStart.value = getNearestHourMoscow();
  eventEnd.value = getNearestHourMoscow();
  eventLocation.value = "";
  eventDesc.value = "";
  eventTags.value = "";
  eventLinks.value = "";
  eventBanner.value = null; // Очищаем картинку

};


</script>

<template>
  <div :class="styles.eventCreatePage">

    <!-- Заголовок -->
    <div :class="styles.pageTitle">Создать событие</div>

    <!-- Карточка изображения -->
    <div :class="styles.imageUpload">
      <div :class="styles.imagePlaceholder">
        <img v-if="eventBanner" :src="eventBanner" alt="Event Image" :class="styles.thumbnail" />

        <label :class="styles.uploadIcon">
          <img src="/icons/add_photo_ae.svg" alt="Upload Image"/>
          <input type="file" ref="fileInput" :class="styles.hidden_input" @change="uploadImage" accept="image/*" />
        </label>

      </div>
    </div>

    <!-- Поля ввода -->
    <div :class="styles.inputGroup">
      <input type="text" :class="styles.inputFieldName" placeholder="Название события" v-model="eventName" />
    </div>

    <div :class="styles.inputGroupDateTime">

      <!-- Начало -->
      <div :class="styles.inputContainer">
        <img src="/icons/start_ae.svg" :class="styles.icon" alt="Начало" />
        <div :class="styles.inputFieldHalf2">Начало</div>
        <input type="datetime-local" :class="styles.inputFieldDatePicker"  v-model="eventStart" />
      </div>

      <div :class="styles.divider"></div>

      <div :class="styles.inputContainer">
        <img src="/icons/end_ae.svg" :class="styles.icon" alt="Конец" />
        <div :class="styles.inputFieldHalf2">Конец</div>
        <input type="datetime-local" :class="styles.inputFieldDatePicker" v-model="eventEnd" />
      </div>

    </div>


    <div :class="styles.inputGroup">
      <div :class="styles.inputContainer">
        <img src="/icons/location_ae.svg" :class="styles.icon" alt="Выберите место" />
       <input type="text" :class="styles.inputField" placeholder="Выберите место" v-model="eventLocation" />
      </div>
    </div>



    <!-- Описание  -->
    <div :class="styles.inputGroup">
      <div :class="styles.inputContainer" >
        <img src="/icons/desc_ae.svg" :class="styles.icon" alt="Добавьте описание" />
      <input type="text" :class="styles.inputField" placeholder="Добавьте описание" v-model="eventDesc" />
      </div>
    </div>

    <!-- Всплывающее окно для ввода описания -->
    <teleport to="body">
      <transition name="fade">
        <div v-if="showDescModal" :class="styles.modal_overlay" @click="closeDescModal">
          <div :class="styles.modal_content" @click.stop>
            <h3>Описание события</h3>
            <textarea
                v-model="tempDesc"
                placeholder="Начните печатать..."
                maxlength="200"
                :class="styles.input_textarea"
            ></textarea>
            <div :class="styles.char_count">{{ tempDesc.length }}/200</div>
            <button @click="saveDescription">Готово</button>
          </div>
        </div>
      </transition>
    </teleport>





    <div :class="styles.comment">
      <div>Используйте теги для вашего мероприятия</div>
      <div>Чем больше тегов, тем точнее алгоритм</div>
    </div>


    <div :class="styles.inputGroup">
      <div :class="styles.inputContainer">
        <img src="/icons/tags_ae.svg" :class="styles.icon" alt="Теги" />
      <input type="text" :class="styles.inputField" placeholder="Теги" v-model="eventTags" />
      </div>
    </div>

    <div :class="styles.comment">
      <div>Вы можете добавить необходимые ссылки</div>
    </div>

    <div :class="styles.inputGroup">
      <div :class="styles.inputContainer">
        <img src="/icons/links_ae.svg" :class="styles.icon" alt="Ссылки" />
      <input type="text" :class="styles.inputField" placeholder="Ссылки" v-model="eventLinks" />
      </div>
    </div>


    <div :class="styles.big_divider"></div>

    <div :class="styles.titleContainer">
      <div :class="styles.title">Билеты</div>
    </div>

    <div :class="styles.inputGroupDateTime">


      <div :class="styles.inputContainer">
        <img src="/icons/approval_ae.svg" :class="styles.icon" alt="Требуется одобрение" />
      <input type="text" :class="styles.inputFieldHalf" placeholder="Требуется одобрение" readonly />

      <label :class="styles.switch">
        <input type="checkbox" v-model="eventApproval" />
        <span :class="styles.slider"></span>
      </label>

      </div>


      <div :class="styles.divider"></div>
      <div :class="styles.inputContainer">
        <img src="/icons/price_ae.svg" :class="styles.icon" alt="Цена" />
      <input type="text" :class="styles.inputFieldHalf" placeholder="Цена" v-model="eventPrice" />
        <select v-model="eventPriceStatus" id="eventPriceStatus">
          <option value="Бесплатно">Бесплатно</option>
          <option value="Платно">Платно</option>
        </select>
        <img src="/icons/up_down.svg" :class="styles.icon" alt="Видимость" />
      </div>
    </div>


    <div :class="styles.titleContainer">
      <div :class="styles.title">Опции</div>
    </div>

    <div :class="styles.inputGroupDateTime">


      <div :class="styles.inputContainer">
        <img src="/icons/visibility_ae.svg" :class="styles.icon" alt="Видимость" />
        <input type="text" :class="styles.inputFieldHalf" placeholder="Видимость" readonly />

        <select v-model="eventVisibility" id="eventVisibility">
          <option value="Публичное">Публичное</option>
          <option value="Частное">Частное</option>
        </select>
        <img src="/icons/up_down.svg" :class="styles.icon" alt="Видимость" />

      </div>


      <div :class="styles.divider"></div>
        <div :class="styles.inputContainer">
          <img src="/icons/capacity_ae.svg" :class="styles.icon" alt="Вместимость" />
      <input type="text" :class="styles.inputFieldHalf" placeholder="Вместимость" />
          <select v-model="eventCapacity" id="eventCapacity">
            <option value="Limited">Limited</option>
            <option value="Unlimited">Unlimited</option>
          </select>
          <img src="/icons/up_down.svg" :class="styles.icon" alt="Видимость" />
        </div>
    </div>




    <!-- Кнопка создания -->
    <button
        :class="[styles.submitButton, isFormValid ? styles.activeButton : styles.disabledButton]"
        :disabled=!isFormValid
        @click="createEvent"
    >
      Создать событие
    </button>


  </div>
</template>

<style scoped>


</style>











