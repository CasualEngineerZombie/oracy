import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import StudentRegisterPage from "./pages/StudentRegisterPage";
import TeacherRegisterPage from "./pages/TeacherRegisterPage";
import PupilDashboard from "./pages/PupilDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import TaskRecordingPage from "./pages/TaskRecordingPage";
import FeedbackPage from "./pages/FeedbackPage";
import TeacherReviewPage from "./pages/TeacherReviewPage";
import ProgressPage from "./pages/ProgressPage";
import NotFound from "./pages/NotFound";
import LiveDemoPage from "./pages/LiveDemoPage";
import StudentManagementPage from "./pages/StudentManagementPage";
import CreateAssessmentPage from "./pages/CreateAssessmentPage";
import { ProtectedRoute } from "./components/AuthGuard";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register/student" element={<StudentRegisterPage />} />
          <Route path="/register/teacher" element={<TeacherRegisterPage />} />
          <Route path="/live-demo" element={<LiveDemoPage />} />
          
          {/* Student Routes - Protected */}
          <Route
            path="/pupil"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <PupilDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pupil/tasks"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <PupilDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pupil/task/:id"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <TaskRecordingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pupil/feedback/:id"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <FeedbackPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pupil/progress"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <ProgressPage role="pupil" />
              </ProtectedRoute>
            }
          />
          
          {/* Teacher Routes - Protected */}
          <Route
            path="/teacher"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/assessments/create"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <CreateAssessmentPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/review"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/review/:id"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <TeacherReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/students"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <StudentManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/progress"
            element={
              <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                <ProgressPage role="teacher" />
              </ProtectedRoute>
            }
          />
          
          {/* Fallback for unknown routes */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
