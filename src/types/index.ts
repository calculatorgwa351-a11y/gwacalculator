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
  author_id?: number
  department?: string | null
  course?: string | null
  timestamp: string
  reactions: Record<string, number>
  comments: Comment[]
  can_edit?: boolean
}

export interface Comment {
  id: number
  content: string
  user: string
  user_id?: number
  timestamp: string
  parent_comment_id?: number | null
  can_delete?: boolean
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

export interface HonorsProgress {
  next_target: string | null
  gap_to_next_target: number | null
  failed_count: number
  above_2_5_count: number
}

export interface DashboardSummary {
  gwa: number | null
  honors: HonorsResult
  honors_progress: HonorsProgress
  grade_count: number
  post_count: number
}

export interface LabeledCount {
  label: string
  count: number
}

export interface GradeDistribution {
  buckets: LabeledCount[]
  total: number
}

export interface AdminStudentDetail {
  id: number
  name: string
  school_id: string
  course?: string
  department?: string
  gwa: number | null
  posts: { id: number; content: string }[]
  grades: SubjectGrade[]
}

export interface PostsFeedResponse {
  items: Post[]
  page: number
  limit: number
  total: number
}

export interface TopBottomResponse {
  top: { id: number; school_id: string; name: string; gwa: number }[]
  bottom: { id: number; school_id: string; name: string; gwa: number }[]
}

export interface AtRiskStudent {
  id: number
  school_id: string
  name: string
  department?: string
  course?: string
  gwa: number | null
  failed_count: number
  reasons: string[]
}

export interface AtRiskResponse {
  items: AtRiskStudent[]
}

export interface AdminAuditEntry {
  id: number
  admin_user_id: number
  admin_name?: string | null
  action: string
  target_type?: string | null
  target_id?: number | null
  meta?: Record<string, unknown>
  timestamp: string
}

export interface AdminAuditResponse {
  items: AdminAuditEntry[]
  page: number
  limit: number
  total: number
}

export interface ThemeState {
  isDark: boolean
}
