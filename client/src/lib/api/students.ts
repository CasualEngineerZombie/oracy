import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

// Types
export interface Student {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  date_of_birth: string | null;
  gender: string | null;
  year_group: number | null;
  eal_status: string | null;
  user: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentListItem {
  id: string;
  full_name: string;
  email: string;
  year_group: number | null;
  created_at: string;
}

export interface Cohort {
  id: string;
  name: string;
  description: string | null;
  teacher: string;
  teacher_name: string;
  academic_year: string | null;
  students: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateStudentRequest {
  first_name: string;
  last_name: string;
  email?: string;
  date_of_birth?: string;
  gender?: string;
  year_group?: number;
  eal_status?: string;
}

export interface CreateCohortRequest {
  name: string;
  description?: string;
  academic_year?: string;
}

export interface AddStudentToCohortRequest {
  student_id: string;
}

// Student hooks
export function useStudents() {
  return useQuery<StudentListItem[]>({
    queryKey: ['students'],
    queryFn: async () => {
      const response = await apiClient.get<StudentListItem[]>('/students/');
      return response.data;
    },
  });
}

export function useStudent(id: string) {
  return useQuery<Student>({
    queryKey: ['student', id],
    queryFn: async () => {
      const response = await apiClient.get<Student>(`/students/${id}/`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useStudentAssessments(studentId: string) {
  return useQuery({
    queryKey: ['studentAssessments', studentId],
    queryFn: async () => {
      const response = await apiClient.get(`/students/${studentId}/assessments/`);
      return response.data;
    },
    enabled: !!studentId,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateStudentRequest): Promise<Student> => {
      const response = await apiClient.post<Student>('/students/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
  });
}

export function useUpdateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CreateStudentRequest> }): Promise<Student> => {
      const response = await apiClient.patch<Student>(`/students/${id}/`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.setQueryData(['student', data.id], data);
    },
  });
}

export function useDeleteStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/students/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
  });
}

// Cohort hooks
export function useCohorts() {
  return useQuery<Cohort[]>({
    queryKey: ['cohorts'],
    queryFn: async () => {
      const response = await apiClient.get<Cohort[]>('/students/cohorts/');
      return response.data;
    },
  });
}

export function useCohort(id: string) {
  return useQuery<Cohort>({
    queryKey: ['cohort', id],
    queryFn: async () => {
      const response = await apiClient.get<Cohort>(`/students/cohorts/${id}/`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateCohort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateCohortRequest): Promise<Cohort> => {
      const response = await apiClient.post<Cohort>('/students/cohorts/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
    },
  });
}

export function useUpdateCohort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CreateCohortRequest> }): Promise<Cohort> => {
      const response = await apiClient.patch<Cohort>(`/students/cohorts/${id}/`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
      queryClient.setQueryData(['cohort', data.id], data);
    },
  });
}

export function useDeleteCohort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/students/cohorts/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
    },
  });
}

export function useAddStudentToCohort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ cohortId, data }: { cohortId: string; data: AddStudentToCohortRequest }) => {
      const response = await apiClient.post(`/students/cohorts/${cohortId}/add_student/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
    },
  });
}

export function useRemoveStudentFromCohort() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ cohortId, data }: { cohortId: string; data: AddStudentToCohortRequest }) => {
      const response = await apiClient.post(`/students/cohorts/${cohortId}/remove_student/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohorts'] });
    },
  });
}
