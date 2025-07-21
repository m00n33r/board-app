import type { RouterConfig } from '@nuxt/schema'

export default <RouterConfig> {
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    // Всегда прокручиваем наверх, игнорируя хэш
    return { top: 0, left: 0 };
  }
}