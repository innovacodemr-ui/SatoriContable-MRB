import { apiClient, isDesktop } from './api';

export interface CostCenter {
  id?: number;
  code: string;
  name: string;
  description?: string;
  parent?: number | null; // ID of the parent
  parent_name?: string; // Optional for display
  is_active: boolean;
}

const getCostCenters = async () => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('get-cost-centers'));
    }
    const response = await apiClient.get('/accounting/cost-centers/');
    return response.data;
};

const createCostCenter = async (costCenter: CostCenter) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('create-cost-center', costCenter));
    }
    const response = await apiClient.post('/accounting/cost-centers/', costCenter);
    return response.data;
};

const updateCostCenter = async (id: number, costCenter: CostCenter) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('update-cost-center', { id, ...costCenter }));
    }
    const response = await apiClient.put(`/accounting/cost-centers/${id}/`, costCenter);
    return response.data;
};

const deleteCostCenter = async (id: number) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('delete-cost-center', id));
    }
    const response = await apiClient.delete(`/accounting/cost-centers/${id}/`);
    return response.data;
};

const accountingService = {
    getCostCenters,
    createCostCenter,
    updateCostCenter,
    deleteCostCenter
};

export default accountingService;
