import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useCurrentUser, isAuthenticated, getUserRole } from '@/lib/api';

interface AuthGuardProps {
  children: ReactNode;
  allowedRoles?: Array<'admin' | 'teacher' | 'student'>;
  fallbackPath?: string;
}

export default function AuthGuard({
  children,
  allowedRoles,
  fallbackPath = '/login',
}: AuthGuardProps) {
  const location = useLocation();
  const { data: user, isLoading } = useCurrentUser();

  // If still loading user data, show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated()) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // If roles are specified, check if user has allowed role
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = getUserRole();
    
    // If user role is not in allowed roles, redirect based on role
    if (userRole && !allowedRoles.includes(userRole as 'admin' | 'teacher' | 'student')) {
      // Redirect to appropriate dashboard based on role
      if (userRole === 'teacher' || userRole === 'admin') {
        return <Navigate to="/teacher" replace />;
      }
      return <Navigate to="/pupil" replace />;
    }

    // If no role yet (shouldn't happen normally), redirect
    if (!userRole) {
      return <Navigate to={fallbackPath} state={{ from: location }} replace />;
    }
  }

  return <>{children}</>;
}

// Helper hook for checking if user can access a route
export function useAuth() {
  const { data: user, isLoading } = useCurrentUser();
  
  return {
    user,
    isLoading,
    isAuthenticated: isAuthenticated(),
    userRole: getUserRole(),
    isTeacher: getUserRole() === 'teacher',
    isStudent: getUserRole() === 'student',
    isAdmin: getUserRole() === 'admin',
  };
}

// Protected route wrapper component
interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  allowedRoles?: Array<'admin' | 'teacher' | 'student'>;
}

export function ProtectedRoute({
  children,
  requireAuth = true,
  allowedRoles,
}: ProtectedRouteProps) {
  const { isLoading, isAuthenticated: authenticated, userRole } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (requireAuth && !authenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    if (!userRole || !allowedRoles.includes(userRole as 'admin' | 'teacher' | 'student')) {
      // Redirect to appropriate dashboard
      if (userRole === 'teacher' || userRole === 'admin') {
        return <Navigate to="/teacher" replace />;
      }
      if (userRole === 'student') {
        return <Navigate to="/pupil" replace />;
      }
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
}
