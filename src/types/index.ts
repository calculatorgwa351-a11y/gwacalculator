export interface User {
  id: number
  school_id: string
  name: string
  department?: string
  course?: string
  is_admin?: boolean
}

export interface Post {
  id: number
  content: string
  author: string
  timestamp: string
  reactions: Record<string, number>
  comments: Comment[]
}

export interface Comment {
  id: number
  content: string
  user: string
  timestamp: string
}

export interface SubjectGrade {
  id: number
  subject: string
  units: number
  grade: number
  year: number
  semester: number
  timestamp: string
  failed: boolean
  gwa?: number
}

export interface GradeUpsert {
  id?: number
  subject: string
  units: number
  grade: number
  year: number
  semester: number
}

export interface Analytics {
  average_gwa: number | null
  failure_rate: number | null
}

export interface HonorsResult {
  eligible: boolean
  reason: string
  title: string | null
  gwa?: number
  status?: string
}

export interface DashboardSummary {
  gwa: number | null
  honors: HonorsResult
  grade_count: number
  post_count: number
}

export interface ThemeState {
  isDark: boolean
}
