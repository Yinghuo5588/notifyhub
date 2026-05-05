<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
import MobileTabBar from '@/components/layout/MobileTabBar.vue'
import MobileMoreSheet from '@/components/layout/MobileMoreSheet.vue'
</script>

<template>
  <div class="relative min-h-screen overflow-x-hidden">
    <div class="flex min-h-screen">
      <Sidebar />

      <main class="flex-1 w-full main-with-mobile-nav">
        <div class="content-wrap">
          <slot />
        </div>
      </main>
    </div>

    <MobileMoreSheet />
    <MobileTabBar />
  </div>
</template>