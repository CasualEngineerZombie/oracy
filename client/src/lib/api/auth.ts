import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, setTokens, clearTokens, getStoredUser, getAccessToken } from './client';

// Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'admin' | 'teacher' | 'student';
  school: string | null;
  subject: string | null;
  is_active: boolean;
  is_verified: boolean;
  date_joined: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface PasswordChangeRequest {
  old_password: string;
  new_password: string;
}

// Auth hooks
export function useLogin() {
  return useMutation({
    mutationFn: async (data: LoginRequest): Promise<LoginResponse> => {
      const response = await apiClient.post<LoginResponse>('/auth/login/', data);
      return response.data;
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token, data.user);
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest): Promise<User> => {
      const response = await apiClient.post<User>('/auth/register/', data);
      return response.data;
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/auth/logout/');
    },
    onSuccess: () => {
      clearTokens();
      queryClient.clear();
    },
    onError: () => {
      // Clear tokens even if the server request fails
      clearTokens();
      queryClient.clear();
    },
  });
}

export function useRefreshToken() {
  return useMutation({
    mutationFn: async (): Promise<RefreshResponse> => {
      const response = await apiClient.post<RefreshResponse>('/auth/refresh/');
      return response.data;
    },
    onSuccess: (data) => {
      const refreshToken = localStorage.getItem('oracy_refresh_token');
      if (refreshToken) {
        setTokens(data.access_token, refreshToken);
      }
    },
  });
}

export function useCurrentUser() {
  return useQuery<User | null>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const token = getAccessToken();
      if (!token) return null;

      // Try to get from server first
      try {
        const response = await apiClient.get<User>('/auth/users/me/');
        const user = response.data;
        localStorage.setItem('oracy_user', JSON.stringify(user));
        return user;
      } catch {
        // Fallback to stored user
        const storedUser = getStoredUser();
        return storedUser;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: PasswordChangeRequest) => {
      const response = await apiClient.post('/auth/users/me/change_password/', data);
      return response.data;
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<User>) => {
      const response = await apiClient.patch('/auth/users/me/update/', data);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('oracy_user', JSON.stringify(data));
      queryClient.setQueryData(['currentUser'], data);
    },
  });
}

// Auth helper to check if user is logged in
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// Auth helper to get user role
export function getUserRole(): string | null {
  const user = getStoredUser();
  return user?.role || null;
}

// Auth helper to check if user is admin
export function isAdmin(): boolean {
  return getUserRole() === 'admin';
}

// Auth helper to check if user is teacher
export function isTeacher(): boolean {
  return getUserRole() === 'teacher';
}
