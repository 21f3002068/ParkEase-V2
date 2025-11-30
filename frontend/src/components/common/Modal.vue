<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal" :class="modalClass">
      <h3>{{ title }}</h3>
      <slot></slot>
      <div class="modal-actions" v-if="!hideActions">
        <button 
          type="submit" 
          :disabled="submitDisabled"
          :class="submitButtonClass"
          @click="$emit('submit')"
        >
          {{ submitText }}
        </button>
        <button 
          type="button" 
          @click="$emit('close')"
          :disabled="submitDisabled"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Modal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      required: true
    },
    submitText: {
      type: String,
      default: 'Submit'
    },
    submitDisabled: {
      type: Boolean,
      default: false
    },
    modalClass: {
      type: String,
      default: ''
    },
    submitButtonClass: {
      type: String,
      default: ''
    },
    hideActions: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'submit']
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}

/* Show scrollbar only on hover */
.modal:hover {
  scrollbar-color: #999 transparent;
}

/* Webkit browsers (Chrome, Safari, Edge) */
.modal::-webkit-scrollbar {
  width: 6px;
}

.modal::-webkit-scrollbar-track {
  background: transparent;
}

.modal::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
}

.modal:hover::-webkit-scrollbar-thumb {
  background: #999;
}

.modal::-webkit-scrollbar-thumb:hover {
  background: #666;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.modal-actions button[type="submit"] {
  background: #007bff;
  color: white;
}

.modal-actions button[type="button"] {
  background: #6c757d;
  color: white;
}

.modal-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Form label and required field styling */
.modal label {
  display: block;
  margin-bottom: 1rem;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.modal label .required {
  color: #dc3545;
  margin-left: 0.25rem;
  font-weight: bold;
  display: inline !important;
  vertical-align: baseline;
}

/* Form input and select styling */
.modal label input,
.modal label select,
.modal label textarea {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  margin-top: 0.25rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

.modal label input:focus,
.modal label select:focus,
.modal label textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modal label select {
  cursor: pointer;
  background-color: white;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  padding-right: 2.5rem;
}

.modal label small {
  display: block;
  margin-top: 0.25rem;
  font-size: 12px;
  color: #6c757d;
  font-weight: normal;
}
</style>