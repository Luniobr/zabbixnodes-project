<template>
  <div class="form-group">
    <label v-if="label" :for="id" class="form-label">{{ label }}</label>

    <div style="position: relative">
      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :required="required"
        :class="['form-control', error ? 'is-invalid' : '']"
        :style="type === 'password' ? 'padding-right: 36px' : ''"
        @input="emit('update:modelValue', $event.target.value)"
      />
      <button
        v-if="type === 'password'"
        type="button"
        @click="showPassword = !showPassword"
        style="
          position: absolute;
          right: 8px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          outline: none;
          cursor: pointer;
          color: var(--text-muted);
          padding: 0;
          display: flex;
        "
      >
        <Transition name="fade" mode="out-in">
          <svg
            v-if="showPassword"
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"
            />
            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
            <line x1="1" y1="1" x2="23" y2="23" />
          </svg>
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </Transition>
      </button>
    </div>
    <span v-if="error" class="form-error">{{ error }}</span>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  id: {
    type: String,
    default: null,
  },
  type: {
    type: String,
    default: 'text',
  },
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  autocomplete: {
    type: String,
    default: 'off',
  },
  required: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: null,
  },
  error: {
    type: String,
    default: null,
  },
})

// Show password if type is password and showPassword is true
const showPassword = ref(false)

const inputType = computed(() => {
  if (props.type !== 'password') return props.type
  return showPassword.value ? 'text' : 'password'
})
const emit = defineEmits(['update:modelValue'])
</script>
<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-50%) scale(0.8);
}

button:focus-visible {
  outline: 2px solid var(--primary);
  border-radius: 4px;
}
</style>
