import { computed } from 'vue'
import type { NoteDetailsItem } from '~/types/notes'

export function useNotes() {
  const { data: notes, pending, error, refresh } = useFetch<NoteDetailsItem[]>('/api/notes')

  return {
    notes: notes,
    status: computed(() => {
      if (pending.value) return 'pending'
      if (error.value) return 'error'
      return 'success'
    }),
    refresh
  }
}