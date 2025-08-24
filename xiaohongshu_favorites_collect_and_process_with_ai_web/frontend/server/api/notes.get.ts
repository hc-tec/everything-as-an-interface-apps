import notesData from '../../data/favorite_notes_details.json'

export default defineEventHandler((event) => {
  return notesData.data
})