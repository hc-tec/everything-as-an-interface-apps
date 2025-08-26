import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineEventHandler, createError, getRouterParam } from 'h3'

function readJson<T = any>(p: string): T | null {
  try {
    const txt = readFileSync(p, 'utf-8')
    return JSON.parse(txt) as T
  } catch (e) {
    return null
  }
}

function resolveDataPath(rel: string) {
  // 1) frontend/data
  const p1 = resolve(process.cwd(), 'data', rel)
  if (existsSync(p1)) return p1
  // 2) project-root/data (../data from frontend)
  const p2 = resolve(process.cwd(), '..', 'data', rel)
  if (existsSync(p2)) return p2
  // 3) fallback: frontend/data (even if not exists, to allow error reporting upstream)
  return p1
}

export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'Missing id' })
  }

  const detailsPath = resolveDataPath('favorite_notes_details.json')
  const aiPath = resolveDataPath('favorite_notes_ai_processed.json')
  const normalizedPath = resolveDataPath('favorite_notes_normalized.json')

  const details = readJson<any>(detailsPath)
  const aiProcessed = readJson<any>(aiPath)
  const normalized = readJson<any>(normalizedPath)

  const aiArray = (aiProcessed as any)?.data as any[] | undefined
  const aiMap = new Map<string, any>()
  if (Array.isArray(aiArray)) {
    for (const item of aiArray) {
      const nid = item?.note_id
      if (nid) aiMap.set(nid, item)
    }
  }

  // normalized: { data: [ { normalized: { note_id, author: { author_link } } } ] }
  const normArray = (normalized as any)?.data as any[] | undefined
  const authorLinkMap = new Map<string, string>()
  if (Array.isArray(normArray)) {
    for (const it of normArray) {
      const nid = it?.normalized?.note_id
      const link = it?.normalized?.author?.author_link
      if (nid && typeof link === 'string') authorLinkMap.set(nid, link)
    }
  }

  const note = ((details as any)?.data || []).find((n: any) => n?.id === id)
  if (!note) {
    throw createError({ statusCode: 404, statusMessage: 'Note not found' })
  }

  const ai = aiMap.get(id)
  let summaryText: string | undefined
  let keywordsArr: string[] | undefined
  let topicsObj: any | undefined

  if (ai) {
    // summary
    summaryText = ai?.summary?.summary_200
      || ai?.tasks?.summary?.result?.summary_200
    // keywords
    keywordsArr = ai?.keywords?.keywords
      || ai?.tasks?.keywords?.result?.keywords
    // topics
    topicsObj = ai?.topics
      || ai?.tasks?.topics?.result
  }

  const out: any = { ...note }

  if (summaryText || (keywordsArr && keywordsArr.length)) {
    out.ai_summary = {
      summary: summaryText || '',
      keywords: Array.isArray(keywordsArr) ? keywordsArr : [],
    }
  }

  if (topicsObj && typeof topicsObj === 'object') {
    out.ai_topics = {
      primary_topic: topicsObj.primary_topic,
      subtopics: topicsObj.subtopics || [],
      content_intent: topicsObj.content_intent,
      content_type: topicsObj.content_type,
      confidence: topicsObj.confidence,
    }
  }

  // inject author_link if available
  const aLink = authorLinkMap.get(id)
  if (aLink) {
    out.author_info = {
      ...out.author_info,
      author_link: aLink,
    }
  }

  return out
})