export type NotifierFieldType =
  | 'text'
  | 'password'
  | 'number'
  | 'checkbox'
  | 'textarea'
  | 'select'
  | 'url'
  | 'json'

export interface NotifierFieldSchema {
  type: NotifierFieldType
  label: string
  required?: boolean
  placeholder?: string
  default?: unknown
  options?: Array<{
    label: string
    value: string | number | boolean
  }>
}

export interface NotifierType {
  type: string
  name: string
  schema: Record<string, NotifierFieldSchema>
}

export interface NotifierConfig {
  id: number
  name: string
  notifier_type: string
  config?: Record<string, unknown>
  is_active: boolean
  is_shared: boolean
  created_at?: string
  updated_at?: string
}