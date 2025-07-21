// composables/usePendingFavorite.ts
export const usePendingFavorite = () => {
  // Создаем глобальное состояние, доступное во всем приложении
  const pendingAction = useState<{ eventId: string | null; action: 'save' | 'unsave' | null }>('pending-favorite-action', () => ({
    eventId: null,
    action: null
  }));
  return pendingAction;
};