import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

function readJson<T = any>(p: string): T | null {
  try {
    const txt = readFileSync(p, 'utf-8')
    return JSON.parse(txt) as T
  } catch (e) {
    return null
  }
}

function resolveDataPath(rel: string) {
  const p1 = resolve(process.cwd(), 'data', rel)
  if (existsSync(p1)) return p1
  const p2 = resolve(process.cwd(), '..', 'data', rel)
  if (existsSync(p2)) return p2
  return p1
}

export default defineEventHandler(() => {
  const detailsPath = resolveDataPath('favorite_notes_details.json')
  const aiPath = resolveDataPath('favorite_notes_ai_processed.json')

  const details = readJson<any>(detailsPath)
  const aiProcessed = readJson<any>(aiPath)

  const aiArray = (aiProcessed as any)?.data as any[] | undefined
  const aiMap = new Map<string, any>()
  if (Array.isArray(aiArray)) {
    for (const item of aiArray) {
      const id = item?.note_id
      if (id) aiMap.set(id, item)
    }
  }

  const counts = {
    primary: new Map<string, number>(),
    subtopics: new Map<string, number>(),
    intents: new Map<string, number>(),
    types: new Map<string, number>(),
  }

  const list = ((details as any)?.data || []) as any[]
  for (const note of list) {
    const ai = aiMap.get(note.id)
    const topics = ai?.topics || ai?.tasks?.topics?.result
    if (!topics) continue
    const primary: string | undefined = topics.primary_topic
    const subs: string[] = Array.isArray(topics.subtopics) ? topics.subtopics : []
    const intent: string | undefined = topics.content_intent
    const type: string | undefined = topics.content_type

    if (primary) counts.primary.set(primary, (counts.primary.get(primary) || 0) + 1)
    for (const s of subs) counts.subtopics.set(s, (counts.subtopics.get(s) || 0) + 1)
    if (intent) counts.intents.set(intent, (counts.intents.get(intent) || 0) + 1)
    if (type) counts.types.set(type, (counts.types.get(type) || 0) + 1)
  }

  function toArray(m: Map<string, number>) {
    return Array.from(m.entries()).map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
  }

  return {
    primary: toArray(counts.primary),
    subtopics: toArray(counts.subtopics),
    intents: toArray(counts.intents),
    types: toArray(counts.types),
  }
})