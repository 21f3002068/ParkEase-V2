<template>
  <div class="table-container">
    <table class="crud-table" v-if="items.length || alwaysShowHeaders">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">
            {{ column.label }}
          </th>
          <th v-if="showActions">Actions</th>
        </tr>
      </thead>
      <tbody v-if="items.length">
        <tr v-for="item in items" :key="item.id || item[keyField]">
          <td v-for="column in columns" :key="column.key">
            <slot :name="`cell-${column.key}`" :item="item" :value="item[column.key]">
              {{ formatCellValue(item[column.key], column) }}
            </slot>
          </td>
          <td v-if="showActions">
            <slot name="actions" :item="item">
              <button 
                v-if="canEdit" 
                @click="$emit('edit', item)"
                class="action-btn edit-btn"
              >
                Edit
              </button>
              <button 
                v-if="canDelete" 
                @click="$emit('delete', item.id || item[keyField])"
                class="action-btn delete-btn"
              >
                Delete
              </button>
            </slot>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td :colspan="columns.length + (showActions ? 1 : 0)" class="empty-state-cell">
            <slot name="empty">
              {{ emptyMessage }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state">
      <slot name="empty">
        {{ emptyMessage }}
      </slot>
    </div>
    
    <!-- Pagination Controls -->
    <div v-if="showPagination && totalPages > 1" class="pagination-controls">
      <button 
        @click="goToPage(currentPage - 1)" 
        :disabled="currentPage === 1"
        class="pagination-btn pagination-arrow"
      >
        <i class="fas fa-chevron-left"></i>
      </button>
      
      <button 
        v-for="page in visiblePages" 
        :key="page"
        @click="page !== '...' && goToPage(page)"
        :class="['pagination-btn', 'pagination-number', { 'active': page === currentPage, 'ellipsis': page === '...' }]"
        :disabled="page === '...'"
      >
        {{ page }}
      </button>
      
      <button 
        @click="goToPage(currentPage + 1)" 
        :disabled="currentPage === totalPages"
        class="pagination-btn pagination-arrow"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DataTable',
  props: {
    items: {
      type: Array,
      required: true
    },
    columns: {
      type: Array,
      required: true
    },
    keyField: {
      type: String,
      default: 'id'
    },
    showActions: {
      type: Boolean,
      default: true
    },
    canEdit: {
      type: Boolean,
      default: true
    },
    canDelete: {
      type: Boolean,
      default: true
    },
    emptyMessage: {
      type: String,
      default: 'No items found.'
    },
    alwaysShowHeaders: {
      type: Boolean,
      default: false
    },
    showPagination: {
      type: Boolean,
      default: false
    },
    currentPage: {
      type: Number,
      default: 1
    },
    totalPages: {
      type: Number,
      default: 1
    }
  },
  emits: ['edit', 'delete', 'page-change'],
  computed: {
    visiblePages() {
      const pages = [];
      const total = this.totalPages;
      const current = this.currentPage;
      
      if (total <= 7) {
        // Show all pages if 7 or fewer
        for (let i = 1; i <= total; i++) {
          pages.push(i);
        }
      } else {
        // Always show first page
        pages.push(1);
        
        if (current > 3) {
          pages.push('...');
        }
        
        // Show pages around current
        const start = Math.max(2, current - 1);
        const end = Math.min(total - 1, current + 1);
        
        for (let i = start; i <= end; i++) {
          pages.push(i);
        }
        
        if (current < total - 2) {
          pages.push('...');
        }
        
        // Always show last page
        pages.push(total);
      }
      
      return pages;
    }
  },
  methods: {
    formatCellValue(value, column) {
      if (column.formatter && typeof column.formatter === 'function') {
        return column.formatter(value);
      }
      return value;
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.$emit('page-change', page);
      }
    }
  }
}
</script>

<style scoped>
.table-container {
  overflow-x: auto;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(102, 126, 234, 0.3) transparent;
}

.table-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: transparent;
}

.table-container::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

.crud-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  flex-shrink: 0;
}

.crud-table th,
.crud-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.crud-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.crud-table tr:hover {
  background-color: #f5f5f5;
}

.action-btn {
  padding: 4px 8px;
  margin: 0 2px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.edit-btn {
  background: #28a745;
  color: white;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
  font-style: italic;
}

.empty-state-cell {
  text-align: center;
  padding: 40px;
  color: #666;
  font-style: italic;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.9rem 0;
  border-top: 1px solid #e1e5e9;
}

.pagination-btn {
  min-width: 28px;
  height: 28px;
  border: 2px solid #e0e0e0;
  background: white;
  color: #333;
  border-radius: 12px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.pagination-btn.pagination-arrow {
  color: #999;
}

.pagination-btn.pagination-number {
  font-weight: 600;
}

.pagination-btn.active {
  background: #4A90E2;
  color: white;
  border-color: #4A90E2;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
}

.pagination-btn:hover:not(:disabled):not(.active):not(.ellipsis) {
  border-color: #4A90E2;
  color: #4A90E2;
  background: rgba(74, 144, 226, 0.05);
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: white;
}

.pagination-btn.ellipsis {
  border: none;
  cursor: default;
  background: transparent;
  color: #999;
}

.pagination-btn.ellipsis:hover {
  border: none;
  background: transparent;
}
</style>