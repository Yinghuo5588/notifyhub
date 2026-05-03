<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

import AuthLayout from '@/layouts/AuthLayout.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import ToastHost from '@/components/ui/ToastHost.vue'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const theme = useThemeStore()

const layoutComponent = computed(() => {
  if (route.meta.layout === 'auth') return AuthLayout
  return DefaultLayout
})

onMounted(() => {
  theme.init()
})
</script>

<template>
  <component :is="layoutComponent">
    <RouterView />
  </component>

  <ToastHost />
</template>