import { http } from './http'
import type {
  Subscription,
  SubscriptionFilter,
  SubscriptionFilterPayload,
  SubscriptionFormOptions,
  SubscriptionUpdatePayload,
} from '@/types/subscription'

export function getSubscriptionsApi() {
  return http.get<Subscription[]>('/subscriptions').then(r => r.data)
}

export function getSubscriptionApi(id: number) {
  return http.get<Subscription>(`/subscriptions/${id}`).then(r => r.data)
}

export function updateSubscriptionApi(id: number, payload: SubscriptionUpdatePayload) {
  return http.put<Subscription>(`/subscriptions/${id}`, payload).then(r => r.data)
}

export function toggleSubscriptionApi(id: number) {
  return http.post<Subscription>(`/subscriptions/${id}/toggle`).then(r => r.data)
}

export function getSubscriptionFormOptionsApi(id: number) {
  return http.get<SubscriptionFormOptions>(`/subscriptions/${id}/form-options`).then(r => r.data)
}

export function createSubscriptionFilterApi(id: number, payload: SubscriptionFilterPayload) {
  return http.post<SubscriptionFilter>(`/subscriptions/${id}/filters`, payload).then(r => r.data)
}

export function updateSubscriptionFilterApi(
  id: number,
  ruleId: number,
  payload: SubscriptionFilterPayload,
) {
  return http
    .put<SubscriptionFilter>(`/subscriptions/${id}/filters/${ruleId}`, payload)
    .then(r => r.data)
}

export function toggleSubscriptionFilterApi(id: number, ruleId: number) {
  return http
    .post<SubscriptionFilter>(`/subscriptions/${id}/filters/${ruleId}/toggle`)
    .then(r => r.data)
}

export function deleteSubscriptionFilterApi(id: number, ruleId: number) {
  return http
    .delete<{ ok: boolean }>(`/subscriptions/${id}/filters/${ruleId}`)
    .then(r => r.data)
}