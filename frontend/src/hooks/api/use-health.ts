import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/lib/api/health';

export function useHealth() {
    return useQuery({
        queryKey: ['health'],
        queryFn: () => healthApi.check(),
        refetchInterval: 30000, // Check every 30 seconds
    });
}
