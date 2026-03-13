import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

// Types
export type AssessmentMode = 'presenting' | 'explaining' | 'persuading';
export type AssessmentStatus = 'draft' | 'recording' | 'uploading' | 'processing' | 'completed' | 'error';

export interface Assessment {
  id: string;
  student: string;
  student_name: string;
  cohort: string;
  cohort_name: string;
  mode: AssessmentMode;
  prompt: string;
  status: AssessmentStatus;
  time_limit_seconds: number;
  consent_obtained: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AssessmentListItem {
  id: string;
  student_name: string;
  cohort_name: string;
  mode: AssessmentMode;
  status: AssessmentStatus;
  created_at: string;
  completed_at: string | null;
}

export interface Transcript {
  segments: Array<{
    start: number;
    end: number;
    text: string;
    confidence: number;
  }>;
  full_text: string;
  language: string;
  confidence: number;
}

export interface FeatureSignals {
  // Fill in based on actual server response
  [key: string]: unknown;
}

export interface EvidenceCandidate {
  candidate_id: string;
  start_time: number;
  end_time: number;
  type: string;
  summary: string;
  transcript_text: string;
  features: Record<string, unknown>;
  relevant_strands: string[];
}

export interface DraftReport {
  id: string;
  physical_score: {
    band: number;
    score: number;
    confidence: number;
    justification: string;
    subskills: Record<string, unknown>;
  };
  linguistic_score: {
    band: number;
    score: number;
    confidence: number;
    justification: string;
    subskills: Record<string, unknown>;
  };
  cognitive_score: {
    band: number;
    score: number;
    confidence: number;
    justification: string;
    subskills: Record<string, unknown>;
  };
  social_emotional_score: {
    band: number;
    score: number;
    confidence: number;
    justification: string;
    subskills: Record<string, unknown>;
  };
  feedback: {
    strengths: string[];
    next_steps: string[];
    goals: string[];
  };
  overall_confidence: number;
  warnings: string[];
  eal_scaffolds: string[];
  is_reviewed: boolean;
  ai_model: string;
  generated_at: string;
}

export interface SignedReport extends Omit<DraftReport, 'is_reviewed'> {
  teacher_notes: string;
  signed_by: string;
  signed_at: string;
  changes_summary: string | null;
}

export interface CreateAssessmentRequest {
  student_id: string;
  cohort_id: string;
  mode: AssessmentMode;
  prompt: string;
  time_limit_seconds?: number;
}

export interface SignOffRequest {
  physical_band?: number;
  physical_clips?: string[];
  linguistic_band?: number;
  linguistic_clips?: string[];
  cognitive_band?: number;
  cognitive_clips?: string[];
  social_emotional_band?: number;
  social_emotional_clips?: string[];
  feedback_strengths?: string[];
  feedback_next_steps?: string[];
  feedback_goals?: string[];
  teacher_notes?: string;
}

// Assessment hooks
export function useAssessments() {
  return useQuery<AssessmentListItem[]>({
    queryKey: ['assessments'],
    queryFn: async () => {
      const response = await apiClient.get<AssessmentListItem[]>('/assessments/');
      return response.data;
    },
  });
}

export function useAssessment(id: string) {
  return useQuery<Assessment>({
    queryKey: ['assessment', id],
    queryFn: async () => {
      const response = await apiClient.get<Assessment>(`/assessments/${id}/`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAssessmentRequest): Promise<Assessment> => {
      const response = await apiClient.post<Assessment>('/assessments/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
    },
  });
}

export interface BulkCreateAssessmentRequest {
  cohort_id: string;
  mode: AssessmentMode;
  prompt: string;
  time_limit_seconds?: number;
}

export function useBulkCreateAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: BulkCreateAssessmentRequest): Promise<{ count: number }> => {
      const response = await apiClient.post<{ count: number }>('/assessments/bulk_create/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
    },
  });
}

export function useUpdateAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CreateAssessmentRequest> }): Promise<Assessment> => {
      const response = await apiClient.patch<Assessment>(`/assessments/${id}/`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
      queryClient.setQueryData(['assessment', data.id], data);
    },
  });
}

export function useDeleteAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/assessments/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
    },
  });
}

export function useUploadRecording() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ assessmentId, file }: { assessmentId: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(`/assessments/${assessmentId}/upload_recording/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', variables.assessmentId] });
    },
  });
}

export function useProcessAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assessmentId: string) => {
      const response = await apiClient.post(`/assessments/${assessmentId}/process/`);
      return response.data;
    },
    onSuccess: (_, assessmentId) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', assessmentId] });
    },
  });
}

export function useAssessmentTranscript(assessmentId: string) {
  return useQuery<Transcript>({
    queryKey: ['assessmentTranscript', assessmentId],
    queryFn: async () => {
      const response = await apiClient.get<Transcript>(`/assessments/${assessmentId}/transcript/`);
      return response.data;
    },
    enabled: !!assessmentId,
  });
}

export function useAssessmentFeatures(assessmentId: string) {
  return useQuery<FeatureSignals>({
    queryKey: ['assessmentFeatures', assessmentId],
    queryFn: async () => {
      const response = await apiClient.get<FeatureSignals>(`/assessments/${assessmentId}/features/`);
      return response.data;
    },
    enabled: !!assessmentId,
  });
}

export function useAssessmentEvidence(assessmentId: string) {
  return useQuery<EvidenceCandidate[]>({
    queryKey: ['assessmentEvidence', assessmentId],
    queryFn: async () => {
      const response = await apiClient.get<EvidenceCandidate[]>(`/assessments/${assessmentId}/evidence/`);
      return response.data;
    },
    enabled: !!assessmentId,
  });
}

export function useAssessmentDraftReport(assessmentId: string) {
  return useQuery<DraftReport>({
    queryKey: ['assessmentDraftReport', assessmentId],
    queryFn: async () => {
      const response = await apiClient.get<DraftReport>(`/assessments/${assessmentId}/draft_report/`);
      return response.data;
    },
    enabled: !!assessmentId,
  });
}

export function useAssessmentSignedReport(assessmentId: string) {
  return useQuery<SignedReport>({
    queryKey: ['assessmentSignedReport', assessmentId],
    queryFn: async () => {
      const response = await apiClient.get<SignedReport>(`/assessments/${assessmentId}/signed_report/`);
      return response.data;
    },
    enabled: !!assessmentId,
  });
}

export function useSignOffAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ assessmentId, data }: { assessmentId: string; data: SignOffRequest }) => {
      const response = await apiClient.post(`/assessments/${assessmentId}/sign_off/`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', variables.assessmentId] });
    },
  });
}

export function useUpdateConsent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ assessmentId, consentObtained }: { assessmentId: string; consentObtained: boolean }) => {
      const response = await apiClient.post(`/assessments/${assessmentId}/update_consent/`, {
        consent_obtained: consentObtained,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', variables.assessmentId] });
    },
  });
}
