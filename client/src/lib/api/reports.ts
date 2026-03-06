import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from './client';

// Types
export interface CohortReport {
  cohort_id: string;
  cohort_name: string;
  generated_at: string;
  total_students: number;
  total_assessments: number;
  average_scores: {
    physical: number;
    linguistic: number;
    cognitive: number;
    social_emotional: number;
    overall: number;
  };
  report_url?: string;
}

// Report hooks
export function useCohortReport(cohortId: string) {
  return useQuery<CohortReport>({
    queryKey: ['cohortReport', cohortId],
    queryFn: async () => {
      const response = await apiClient.get<CohortReport>(`/reports/cohorts/${cohortId}/`);
      return response.data;
    },
    enabled: !!cohortId,
  });
}

export function useExportCohortReport() {
  return useMutation({
    mutationFn: async (cohortId: string) => {
      const response = await apiClient.get(`/reports/cohorts/export/`, {
        params: { cohort_id: cohortId },
        responseType: 'blob',
      });
      return response.data;
    },
  });
}
