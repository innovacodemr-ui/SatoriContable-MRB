import { apiClient as api } from './api';

export interface DashboardMetrics {
    period: string;
    sales_month: number;
    expenses_month: number;
    available_cash: number;
    chart_data: {
        name: string;
        value: number;
        fill?: string;
    }[];
}

export const reportsService = {
    getDashboardMetrics: async (): Promise<DashboardMetrics> => {
        const response = await api.get('/reports/dashboard/');
        return response.data;
    }
};
