# Frontend Structure (React)

## Project Structure

```
client/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component
│   ├── routes.tsx                  # Route definitions
│   │
│   ├── api/                        # API client
│   │   ├── client.ts               # Axios instance
│   │   ├── auth.ts                 # Auth endpoints
│   │   ├── assessments.ts          # Assessment endpoints
│   │   ├── students.ts             # Student endpoints
│   │   ├── reports.ts              # Report endpoints
│   │   └── types.ts                # API type definitions
│   │
│   ├── components/                 # Reusable components
│   │   ├── ui/                     # Base UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loading.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── layout/                 # Layout components
│   │   │   ├── MainLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── video/                  # Video-related components
│   │   │   ├── VideoRecorder.tsx   # WebRTC recording
│   │   │   ├── VideoPlayer.tsx     # Video playback
│   │   │   ├── VideoTimeline.tsx   # Timestamp navigation
│   │   │   ├── ClipSelector.tsx    # Evidence clip selection
│   │   │   └── index.ts
│   │   │
│   │   ├── assessment/             # Assessment components
│   │   │   ├── AssessmentCard.tsx
│   │   │   ├── AssessmentList.tsx
│   │   │   ├── AssessmentForm.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── report/                 # Report components
│   │   │   ├── ReportViewer.tsx
│   │   │   ├── StrandScore.tsx
│   │   │   ├── EvidenceClips.tsx
│   │   │   ├── FeedbackSection.tsx
│   │   │   ├── ScoreEditor.tsx
│   │   │   └── index.ts
│   │   │
│   │   └── dashboard/              # Dashboard components
│   │       ├── StatsCard.tsx
│   │       ├── RecentAssessments.tsx
│   │       ├── CohortSelector.tsx
│   │       └── index.ts
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useAuth.ts              # Authentication state
│   │   ├── useApi.ts               # API request wrapper
│   │   ├── useVideoRecorder.ts     # Recording logic
│   │   ├── useAssessment.ts        # Assessment data
│   │   ├── useReport.ts            # Report data
│   │   └── index.ts
│   │
│   ├── pages/                      # Page components
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── dashboard/
│   │   │   ├── DashboardPage.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── students/
│   │   │   ├── StudentsListPage.tsx
│   │   │   ├── StudentDetailPage.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── assessments/
│   │   │   ├── AssessmentListPage.tsx
│   │   │   ├── AssessmentCreatePage.tsx
│   │   │   ├── AssessmentRecordPage.tsx
│   │   │   ├── AssessmentReviewPage.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── reports/
│   │   │   ├── ReportViewPage.tsx
│   │   │   ├── ReportEditPage.tsx
│   │   │   └── index.ts
│   │   │
│   │   └── settings/
│   │       ├── SettingsPage.tsx
│   │       └── index.ts
│   │
│   ├── stores/                     # Zustand stores
│   │   ├── authStore.ts            # Auth state
│   │   ├── assessmentStore.ts      # Assessment state
│   │   ├── uiStore.ts              # UI state (modals, toasts)
│   │   └── index.ts
│   │
│   ├── utils/                      # Utility functions
│   │   ├── formatters.ts           # Date, time formatters
│   │   ├── validators.ts           # Form validation
│   │   ├── constants.ts            # App constants
│   │   └── index.ts
│   │
│   ├── types/                      # TypeScript types
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── student.ts
│   │   ├── assessment.ts
│   │   ├── report.ts
│   │   └── index.ts
│   │
│   └── styles/                     # Global styles
│       ├── index.css               # Tailwind imports
│       └── variables.css           # CSS variables
│
├── tests/                          # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env                            # Environment variables
├── .env.example
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── eslint.config.js
└── playwright.config.ts
```

---

## Component Architecture

### Core UI Components

#### Button.tsx
```tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700',
        secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
        danger: 'bg-red-600 text-white hover:bg-red-700',
        ghost: 'hover:bg-gray-100',
      },
      size: {
        sm: 'h-8 px-3',
        md: 'h-10 px-4',
        lg: 'h-12 px-6',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant,
  size,
  isLoading,
  disabled,
  ...props
}) => {
  return (
    <button
      className={buttonVariants({ variant, size })}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <LoadingSpinner className="mr-2" />}
      {children}
    </button>
  );
};
```

### Video Components

#### VideoRecorder.tsx
```tsx
import React, { useRef, useState, useCallback } from 'react';

interface VideoRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
  maxDuration?: number; // seconds
  countdown?: number; // countdown before recording
}

export const VideoRecorder: React.FC<VideoRecorderProps> = ({
  onRecordingComplete,
  maxDuration = 180,
  countdown = 3,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  
  const [isRecording, setIsRecording] = useState(false);
  const [isCountingDown, setIsCountingDown] = useState(false);
  const [countdownValue, setCountdownValue] = useState(countdown);
  const [recordingTime, setRecordingTime] = useState(0);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  const initializeCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'user' },
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setError('Unable to access camera. Please check permissions.');
    }
  }, []);

  const startCountdown = useCallback(() => {
    setIsCountingDown(true);
    setCountdownValue(countdown);
    
    const timer = setInterval(() => {
      setCountdownValue((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsCountingDown(false);
          startRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [countdown]);

  const startRecording = useCallback(() => {
    if (!stream) return;
    
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'video/webm;codecs=vp9,opus',
    });
    
    mediaRecorderRef.current = mediaRecorder;
    chunksRef.current = [];
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      onRecordingComplete(blob);
    };
    
    mediaRecorder.start(1000); // Collect data every second
    setIsRecording(true);
    
    // Timer for recording duration
    const timer = setInterval(() => {
      setRecordingTime((prev) => {
        if (prev >= maxDuration) {
          stopRecording();
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  }, [stream, maxDuration, onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all tracks
      stream?.getTracks().forEach(track => track.stop());
    }
  }, [isRecording, stream]);

  return (
    <div className="relative rounded-lg overflow-hidden bg-black">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="w-full aspect-video"
      />
      
      {isCountingDown && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <span className="text-6xl font-bold text-white">{countdownValue}</span>
        </div>
      )}
      
      {isRecording && (
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <span className="text-white font-mono">
            {Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}
          </span>
        </div>
      )}
      
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-4">
        {!isRecording && !isCountingDown && (
          <Button onClick={startCountdown} size="lg">
            Start Recording
          </Button>
        )}
        
        {isRecording && (
          <Button variant="danger" onClick={stopRecording} size="lg">
            Stop Recording
          </Button>
        )}
      </div>
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <p className="text-white text-center px-4">{error}</p>
        </div>
      )}
    </div>
  );
};
```

#### VideoPlayer with Timeline
```tsx
import React, { useRef, useState, useCallback } from 'react';

interface Clip {
  id: string;
  start: number;
  end: number;
  type: string;
}

interface VideoPlayerProps {
  src: string;
  clips?: Clip[];
  onClipClick?: (clip: Clip) => void;
  activeClipId?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  clips = [],
  onClipClick,
  activeClipId,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  }, []);

  const seekTo = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  }, []);

  const playClip = useCallback((clip: Clip) => {
    if (videoRef.current) {
      videoRef.current.currentTime = clip.start;
      videoRef.current.play();
      setIsPlaying(true);
      
      // Auto-pause at end of clip
      const checkEnd = () => {
        if (videoRef.current && videoRef.current.currentTime >= clip.end) {
          videoRef.current.pause();
          setIsPlaying(false);
          videoRef.current.removeEventListener('timeupdate', checkEnd);
        }
      };
      
      videoRef.current.addEventListener('timeupdate', checkEnd);
    }
    
    onClipClick?.(clip);
  }, [onClipClick]);

  return (
    <div className="space-y-4">
      <video
        ref={videoRef}
        src={src}
        className="w-full rounded-lg"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        controls
      />
      
      {/* Timeline with clips */}
      <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
        {/* Progress bar */}
        <div
          className="absolute h-full bg-blue-200"
          style={{ width: `${(currentTime / duration) * 100}%` }}
        />
        
        {/* Clip markers */}
        {clips.map((clip) => (
          <button
            key={clip.id}
            onClick={() => playClip(clip)}
            className={`absolute h-full transition-colors ${
              clip.id === activeClipId
                ? 'bg-green-500'
                : 'bg-blue-500 hover:bg-blue-600'
            }`}
            style={{
              left: `${(clip.start / duration) * 100}%`,
              width: `${((clip.end - clip.start) / duration) * 100}%`,
            }}
            title={`${clip.type}: ${clip.start.toFixed(1)}s - ${clip.end.toFixed(1)}s`}
          />
        ))}
        
        {/* Time markers */}
        <div className="absolute bottom-0 left-0 right-0 flex justify-between px-2 text-xs text-gray-500">
          <span>0:00</span>
          <span>{Math.floor(duration / 60)}:{String(Math.floor(duration % 60)).padStart(2, '0')}</span>
        </div>
      </div>
      
      {/* Clip list */}
      {clips.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700">Evidence Clips</h4>
          <div className="flex flex-wrap gap-2">
            {clips.map((clip) => (
              <button
                key={clip.id}
                onClick={() => playClip(clip)}
                className={`px-3 py-1 text-sm rounded-full transition-colors ${
                  clip.id === activeClipId
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {clip.start.toFixed(1)}s - {clip.end.toFixed(1)}s
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## State Management

### Auth Store (Zustand)
```ts
// stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'teacher' | 'student';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),
      
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
      
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

### Assessment Store
```ts
// stores/assessmentStore.ts
import { create } from 'zustand';

interface Assessment {
  id: string;
  studentId: string;
  mode: 'presenting' | 'explaining' | 'persuading';
  prompt: string;
  status: string;
  createdAt: string;
}

interface AssessmentState {
  assessments: Assessment[];
  currentAssessment: Assessment | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAssessments: (assessments: Assessment[]) => void;
  setCurrentAssessment: (assessment: Assessment | null) => void;
  addAssessment: (assessment: Assessment) => void;
  updateAssessment: (id: string, updates: Partial<Assessment>) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAssessmentStore = create<AssessmentState>((set) => ({
  assessments: [],
  currentAssessment: null,
  isLoading: false,
  error: null,
  
  setAssessments: (assessments) => set({ assessments }),
  setCurrentAssessment: (assessment) => set({ currentAssessment: assessment }),
  addAssessment: (assessment) =>
    set((state) => ({
      assessments: [assessment, ...state.assessments],
    })),
  updateAssessment: (id, updates) =>
    set((state) => ({
      assessments: state.assessments.map((a) =>
        a.id === id ? { ...a, ...updates } : a
      ),
    })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
```

---

## API Client

### Axios Instance
```ts
// api/client.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = useAuthStore.getState().refreshToken;
      
      try {
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh/`,
          { refresh: refreshToken }
        );
        
        const { access } = response.data;
        useAuthStore.getState().accessToken = access;
        
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

### API Hooks
```ts
// hooks/useApi.ts
import { useState, useCallback } from 'react';
import apiClient from '@/api/client';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export function useApi<T>(options: UseApiOptions = {}) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(
    async (method: string, url: string, body?: any) => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiClient.request({
          method,
          url,
          data: body,
        });
        
        setData(response.data);
        options.onSuccess?.(response.data);
        return response.data;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options.onError?.(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [options]
  );

  return { data, isLoading, error, execute };
}

// Specialized hooks
export function useGet<T>(url: string) {
  const api = useApi<T>();
  
  const get = useCallback(() => {
    return api.execute('GET', url);
  }, [url]);
  
  return { ...api, get };
}

export function usePost<T>(url: string, options?: UseApiOptions) {
  const api = useApi<T>(options);
  
  const post = useCallback(
    (body: any) => {
      return api.execute('POST', url, body);
    },
    [url]
  );
  
  return { ...api, post };
}
```

---

## Routing

```tsx
// routes.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout';
import { ProtectedRoute } from '@/components/auth';

// Pages
import { LoginPage } from '@/pages/auth';
import { DashboardPage } from '@/pages/dashboard';
import { StudentsListPage, StudentDetailPage } from '@/pages/students';
import {
  AssessmentListPage,
  AssessmentCreatePage,
  AssessmentRecordPage,
  AssessmentReviewPage,
} from '@/pages/assessments';
import { ReportViewPage, ReportEditPage } from '@/pages/reports';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'students',
        children: [
          { index: true, element: <StudentsListPage /> },
          { path: ':id', element: <StudentDetailPage /> },
        ],
      },
      {
        path: 'assessments',
        children: [
          { index: true, element: <AssessmentListPage /> },
          { path: 'new', element: <AssessmentCreatePage /> },
          { path: ':id/record', element: <AssessmentRecordPage /> },
          { path: ':id/review', element: <AssessmentReviewPage /> },
        ],
      },
      {
        path: 'reports',
        children: [
          { path: ':assessmentId', element: <ReportViewPage /> },
          { path: ':assessmentId/edit', element: <ReportEditPage /> },
        ],
      },
    ],
  },
]);
```

---

## Key Features Implementation

### Real-time Status Updates (WebSocket)
```tsx
// hooks/useAssessmentStatus.ts
import { useEffect, useRef } from 'react';
import { useAssessmentStore } from '@/stores/assessmentStore';

export function useAssessmentStatus(assessmentId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const updateAssessment = useAssessmentStore((state) => state.updateAssessment);

  useEffect(() => {
    const wsUrl = `${import.meta.env.VITE_WS_URL}/assessments/${assessmentId}/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'status_update') {
        updateAssessment(assessmentId, {
          status: data.status,
          statusMessage: data.message,
        });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [assessmentId, updateAssessment]);
}
```

### Video Upload with Progress
```tsx
// components/video/VideoUploader.tsx
import React, { useState, useCallback } from 'react';
import axios from 'axios';

interface VideoUploaderProps {
  assessmentId: string;
  onUploadComplete: () => void;
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({
  assessmentId,
  onUploadComplete,
}) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const uploadVideo = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setUploadProgress(0);

      try {
        // 1. Get presigned URL from backend
        const { data } = await axios.post(
          `/api/assessments/${assessmentId}/upload-url/`,
          {
            filename: file.name,
            contentType: file.type,
            fileSize: file.size,
          }
        );

        // 2. Upload directly to S3
        await axios.put(data.uploadUrl, file, {
          headers: {
            'Content-Type': file.type,
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            setUploadProgress(progress);
          },
        });

        // 3. Notify backend upload is complete
        await axios.post(
          `/api/assessments/${assessmentId}/complete-upload/`,
          {
            s3Key: data.s3Key,
          }
        );

        onUploadComplete();
      } catch (error) {
        console.error('Upload failed:', error);
        // Show error toast
      } finally {
        setIsUploading(false);
      }
    },
    [assessmentId, onUploadComplete]
  );

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept="video/*"
        onChange={(e) => e.target.files?.[0] && uploadVideo(e.target.files[0])}
        disabled={isUploading}
      />
      
      {isUploading && (
        <div className="space-y-2">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600">{uploadProgress}% uploaded</p>
        </div>
      )}
    </div>
  );
};
```

---

## Styling (Tailwind)

### tailwind.config.js
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        strand: {
          physical: '#ef4444',      // Red
          linguistic: '#3b82f6',    // Blue
          cognitive: '#22c55e',     // Green
          social: '#a855f7',        // Purple
        },
        band: {
          emerging: '#f97316',      // Orange
          expected: '#22c55e',      // Green
          exceeding: '#3b82f6',     // Blue
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

---

## Testing

### Unit Tests (Vitest)
```ts
// tests/unit/components/Button.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('is disabled when isLoading is true', () => {
    render(<Button isLoading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### E2E Tests (Playwright)
```ts
// tests/e2e/assessment.spec.ts
import { test, expect } from '@playwright/test';

test('teacher can create and submit assessment', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'teacher@school.edu');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Navigate to new assessment
  await page.click('text=New Assessment');
  
  // Fill form
  await page.selectOption('select[name="student"]', 'student-123');
  await page.selectOption('select[name="mode"]', 'explaining');
  await page.fill('textarea[name="prompt"]', 'Explain photosynthesis');
  
  // Submit
  await page.click('button[type="submit"]');
  
  // Verify redirect to recording page
  await expect(page).toHaveURL(/\/assessments\/.*\/record/);
});
```
