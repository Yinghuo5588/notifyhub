export interface User {
  id: number
  username: string
  email?: string
  is_admin: boolean
  is_active: boolean
  must_change_pwd: boolean
  created_at?: string
}