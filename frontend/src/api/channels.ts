import { http } from './http'
import type { Channel } from '@/types/channel'

export function getChannelsApi() {
  return http.get<Channel[]>('/channels').then(r => r.data)
}

export function deleteChannelApi(id: number) {
  return http.delete<{ ok: boolean }>(`/channels/${id}`).then(r => r.data)
}