<template>
  <div class="layout">
    <AppTopbar />
    <div class="sidebar">
      <AppSidebar />
    </div>
    <div class="content">
      <RouterView />
    </div>
  </div>
</template>

<script setup>
import AppTopbar from './AppTopbar.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<style></style>
