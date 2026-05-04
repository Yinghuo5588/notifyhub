export interface NotificationTemplate {
  id: number
  name: string
  description: string
  body_format: 'text' | 'html' | string
  is_shared: boolean
  subject_template?: string
  body_template?: string
  sample_data?: string
  variables?: string[]
  created_at?: string | null
  updated_at?: string | null
}

export interface TemplatePayload {
  name: string
  description: string
  subject_template: string
  body_template: string
  body_format: 'text' | 'html'
  sample_data: string
  is_shared: boolean
}

export interface TemplatePreviewPayload {
  subject_template: string
  body_template: string
  sample_data: string
}

export interface TemplatePreviewResp {
  subject: string
  body: string
}