export interface NotificationTemplate {
  id: number
  name: string
  description: string
  body_format: string
  is_shared: boolean
  subject_template?: string
  body_template?: string
  sample_data?: string
  created_at?: string | null
  updated_at?: string | null
}