import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';

export function useDashboardData() {
    return useQuery({
        queryKey: ['analytics', 'dashboard'],
        queryFn: () => analyticsApi.getDashboard(),
    });
}

export function useReports() {
    return useQuery({
        queryKey: ['analytics', 'reports'],
        queryFn: () => analyticsApi.listReports(),
    });
}

export function useReport(reportId: string) {
    return useQuery({
        queryKey: ['analytics', 'reports', reportId],
        queryFn: () => analyticsApi.getReport(reportId),
        enabled: Boolean(reportId),
    });
}

export function useMetrics(period: string = '24h') {
    return useQuery({
        queryKey: ['analytics', 'metrics', period],
        queryFn: () => analyticsApi.getMetrics(period),
    });
}
