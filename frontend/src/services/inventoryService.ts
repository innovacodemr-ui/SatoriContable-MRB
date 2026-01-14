import { apiClient, isDesktop } from './api';

export interface Item {
  id?: number;
  code: string;
  description: string;
  unit_price: number;
  type: 'PRODUCTO' | 'SERVICIO';
  tax_type: 'IVA_19' | 'IVA_5' | 'EXENTO' | 'EXCLUIDO';
  is_active: boolean;
}

const getItems = async (search?: string) => {
    if (isDesktop()) {
        const query = search ? { search } : {};
        return (await window.electronAPI!.invoke('get-items', query));
    }
    const params = search ? { search } : {};
    const response = await apiClient.get('/invoicing/items/', { params });
    return response.data;
};

const createItem = async (item: Item) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('create-item', item));
    }
    const response = await apiClient.post('/invoicing/items/', item);
    return response.data;
};

const updateItem = async (id: number, item: Item) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('update-item', { id, ...item }));
    }
    const response = await apiClient.put(`/invoicing/items/${id}/`, item);
    return response.data;
};

const deleteItem = async (id: number) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('delete-item', id));
    }
    const response = await apiClient.delete(`/invoicing/items/${id}/`);
    return response.data;
};

const inventoryService = {
    getItems,
    createItem,
    updateItem,
    deleteItem
};

export default inventoryService;
