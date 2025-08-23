import { ref, onMounted, readonly } from 'vue'

export const useTelegram = () => {
  const user = ref(null)
  const isReady = ref(false)
  const error = ref(null)

  const getUserFromHash = () => {
    try {
      // Пытаемся получить user_id из хэша URL
      const urlParams = new URLSearchParams(window.location.hash.substring(1))
      const initData = urlParams.get('tgWebAppData')
      
      if (initData) {
        // Парсим initData для получения user_id
        const params = new URLSearchParams(initData)
        const userData = params.get('user')
        
        if (userData) {
          try {
            const userObj = JSON.parse(decodeURIComponent(userData))
            return userObj
          } catch (e) {
            console.warn('Не удалось распарсить user данные из хэша:', e)
          }
        }
      }
    } catch (e) {
      console.warn('Ошибка при получении user_id из хэша:', e)
    }
    return null
  }

  const initTelegram = () => {
    return new Promise((resolve, reject) => {
      // Проверяем, доступен ли Telegram WebApp
      if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
        try {
          window.Telegram.WebApp.ready()
          
          const userData = window.Telegram.WebApp.initDataUnsafe?.user
          if (userData) {
            user.value = userData
            isReady.value = true
            resolve(userData)
          } else {
            // Пробуем получить из хэша как fallback
            const fallbackUser = getUserFromHash()
            if (fallbackUser) {
              user.value = fallbackUser
              isReady.value = true
              resolve(fallbackUser)
            } else {
              error.value = 'Не удалось получить данные пользователя'
              reject(new Error('Не удалось получить данные пользователя'))
            }
          }
        } catch (e) {
          error.value = e.message
          reject(e)
        }
      } else {
        // Если Telegram WebApp не доступен, пробуем получить из хэша
        const fallbackUser = getUserFromHash()
        if (fallbackUser) {
          user.value = fallbackUser
          isReady.value = true
          resolve(fallbackUser)
        } else {
          error.value = 'Telegram WebApp не доступен'
          reject(new Error('Telegram WebApp не доступен'))
        }
      }
    })
  }

  const waitForTelegram = () => {
    return new Promise((resolve) => {
      const checkTelegram = () => {
        if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
          resolve()
        } else {
          setTimeout(checkTelegram, 100)
        }
      }
      checkTelegram()
    })
  }

  onMounted(async () => {
    try {
      await waitForTelegram()
      await initTelegram()
    } catch (e) {
      console.error('Ошибка инициализации Telegram:', e)
    }
  })

  return {
    user: readonly(user),
    isReady: readonly(isReady),
    error: readonly(error),
    initTelegram,
    waitForTelegram
  }
}