<template>
  <button :class="classes" :type="props.type" :disabled="props.disabled || props.loading">
    <span v-if="props.loading" class="spinner" />
    <div v-show="!props.loading"><slot /></div>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
  },
  size: {
    type: String,
    default: 'md',
  },
  type: {
    type: String,
    default: 'button',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const classes = computed(() => ['btn', `btn-${props.variant}`, props.size === 'sm' ? 'btn-sm' : ''])
</script>

<style></style>
