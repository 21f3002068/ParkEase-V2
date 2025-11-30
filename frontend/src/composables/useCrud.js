import { ref, reactive } from 'vue';
import { ApiError } from '@/utils/api';

export function useCrud(api, options = {}) {
    const items = ref([]);
    const loading = ref(false);
    const error = ref('');
    const success = ref('');

    // Form state
    const showAddModal = ref(false);
    const showEditModal = ref(false);
    const form = reactive(options.defaultForm || {});
    const originalForm = { ...form };

    // Reset form to default values
    const resetForm = () => {
        Object.keys(originalForm).forEach(key => {
            form[key] = originalForm[key];
        });
    };

    // Fetch all items
    const fetchItems = async () => {
        loading.value = true;
        error.value = '';
        try {
            const data = await api.getAll();
            items.value = options.mapResponse ? options.mapResponse(data) : data;
        } catch (err) {
            error.value = err.message || 'Failed to fetch items';
            console.error('Error fetching items:', err);
        } finally {
            loading.value = false;
        }
    };

    // Add new item
    const addItem = async () => {
        loading.value = true;
        error.value = '';
        success.value = '';
        try {
            const payload = options.mapRequest ? options.mapRequest(form) : form;
            const data = await api.create(payload);
            success.value = data.message || 'Item added successfully!';
            await fetchItems();
            closeModal();
            if (options.onSuccess) options.onSuccess('add', data);
        } catch (err) {
            error.value = err.message || 'Failed to add item';
            if (options.onError) options.onError('add', err);
        } finally {
            loading.value = false;
        }
    };

    // Edit item
    const editItem = (item) => {
        Object.keys(form).forEach(key => {
            if (item.hasOwnProperty(key)) {
                form[key] = item[key];
            }
        });
        showEditModal.value = true;
        showAddModal.value = false;
    };

    // Update item
    const updateItem = async () => {
        loading.value = true;
        error.value = '';
        success.value = '';
        try {
            const payload = options.mapRequest ? options.mapRequest(form) : form;
            const data = await api.update(form.id, payload);
            success.value = data.message || 'Item updated successfully!';
            await fetchItems();
            closeModal();
            if (options.onSuccess) options.onSuccess('update', data);
        } catch (err) {
            error.value = err.message || 'Failed to update item';
            if (options.onError) options.onError('update', err);
        } finally {
            loading.value = false;
        }
    };

    // Delete item
    const deleteItem = async (id) => {
        if (!confirm('Are you sure you want to delete this item?')) return;

        loading.value = true;
        error.value = '';
        success.value = '';
        try {
            const data = await api.delete(id);
            success.value = data.message || 'Item deleted successfully!';
            await fetchItems();
            if (options.onSuccess) options.onSuccess('delete', data);
        } catch (err) {
            error.value = err.message || 'Failed to delete item';
            if (options.onError) options.onError('delete', err);
        } finally {
            loading.value = false;
        }
    };

    // Modal management
    const openAddModal = () => {
        resetForm();
        showAddModal.value = true;
        showEditModal.value = false;
    };

    const closeModal = () => {
        showAddModal.value = false;
        showEditModal.value = false;
        resetForm();
        error.value = '';
        success.value = '';
    };

    // Submit handler (determines add vs update)
    const submitForm = async () => {
        if (showEditModal.value) {
            await updateItem();
        } else {
            await addItem();
        }
    };

    return {
        // Data
        items,
        loading,
        error,
        success,
        form,

        // Modal state
        showAddModal,
        showEditModal,

        // Methods
        fetchItems,
        addItem,
        editItem,
        updateItem,
        deleteItem,
        openAddModal,
        closeModal,
        submitForm,
        resetForm
    };
}