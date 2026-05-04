import { http } from './http'
import type {
  Channel,
  ChannelFormOptions,
  ChannelPayload,
  FilterRule,
  FilterRulePayload,
} from '@/types/channel'

export function getChannelsApi() {
  return http.get<Channel[]>('/channels').then(r => r.data)
}

export function getChannelApi(id: number) {
  return http.get<Channel>(`/channels/${id}`).then(r => r.data)
}

export function createChannelApi(payload: ChannelPayload) {
  return http.post<Channel>('/channels', payload).then(r => r.data)
}

export function updateChannelApi(id: number, payload: ChannelPayload) {
  return http.put<Channel>(`/channels/${id}`, payload).then(r => r.data)
}

export function deleteChannelApi(id: number) {
  return http.delete<{ ok: boolean }>(`/channels/${id}`).then(r => r.data)
}

export function regenerateChannelTokenApi(id: number) {
  return http.post<Channel>(`/channels/${id}/regenerate-token`).then(r => r.data)
}

export function getChannelFormOptionsApi() {
  return http.get<ChannelFormOptions>('/channels/form-options').then(r => r.data)
}

export function createChannelFilterApi(channelId: number, payload: FilterRulePayload) {
  return http.post<FilterRule>(`/channels/${channelId}/filters`, payload).then(r => r.data)
}

export function updateChannelFilterApi(
  channelId: number,
  ruleId: number,
  payload: FilterRulePayload,
) {
  return http
    .put<FilterRule>(`/channels/${channelId}/filters/${ruleId}`, payload)
    .then(r => r.data)
}

export function toggleChannelFilterApi(channelId: number, ruleId: number) {
  return http
    .post<FilterRule>(`/channels/${channelId}/filters/${ruleId}/toggle`)
    .then(r => r.data)
}

export function deleteChannelFilterApi(channelId: number, ruleId: number) {
  return http
    .delete<{ ok: boolean }>(`/channels/${channelId}/filters/${ruleId}`)
    .then(r => r.data)
}