import { useMutation } from '@tanstack/react-query';
import { predictionsApi } from '@/lib/api/predictions';
import type {
    PredictionRequest,
    BatchPredictionRequest,
    AnomalyDetectionRequest,
    ForecastRequest,
    ChurnPredictionRequest,
} from '@/types/api';

export function usePredict() {
    return useMutation({
        mutationFn: (data: PredictionRequest) => predictionsApi.predict(data),
    });
}

export function useBatchPredict() {
    return useMutation({
        mutationFn: (data: BatchPredictionRequest) => predictionsApi.batchPredict(data),
    });
}

export function useDetectAnomaly() {
    return useMutation({
        mutationFn: (data: AnomalyDetectionRequest) => predictionsApi.detectAnomaly(data),
    });
}

export function useGenerateForecast() {
    return useMutation({
        mutationFn: (data: ForecastRequest) => predictionsApi.generateForecast(data),
    });
}

export function usePredictChurn() {
    return useMutation({
        mutationFn: (data: ChurnPredictionRequest) => predictionsApi.predictChurn(data),
    });
}
