<template>
  <h1 class="title-page">{{ props.title }}</h1>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true,
  },
})
</script>

<style>
.title-page {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 1rem;
}
</style>
