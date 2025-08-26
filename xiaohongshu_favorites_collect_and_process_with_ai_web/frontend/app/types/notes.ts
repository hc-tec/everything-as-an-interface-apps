export interface AuthorInfo {
  user_id: string
  username: string
  avatar: string
  xsec_token: string
  author_link?: string
}

export interface NoteStatistics {
  like_num: string
  collect_num: string
  chat_num: string
}

export interface VideoInfo {
  duration_sec: number
  src: string
  id: string
}

export interface AiSummary {
  summary: string
  keywords: string[]
}

export interface AiTopics {
  primary_topic: string
  subtopics: string[]
  content_intent: string
  content_type: string
  confidence?: number
}

export interface NoteDetailsItem {
  id: string
  title: string
  desc: string
  author_info: AuthorInfo
  tags: string[]
  date: number
  ip_zh: string | null
  comment_num: string
  statistic: NoteStatistics
  images: string[] | null
  video: VideoInfo | null
  timestamp: string
  ai_summary?: AiSummary
  ai_topics?: AiTopics
  platform?: string // Added platform as it was in the user request but not in the json
}