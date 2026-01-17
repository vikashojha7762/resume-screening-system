import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { store } from './store';
import { useAppSelector } from './store/hooks';
import { lightTheme, darkTheme } from './theme/theme';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/layout/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

// Lazy load pages for code splitting
const JobsPage = React.lazy(() => import('./pages/Jobs'));
const JobDetailPage = React.lazy(() => import('./pages/JobDetail'));
const JobFormPage = React.lazy(() => import('./pages/JobForm'));
const ResumesPage = React.lazy(() => import('./pages/Resumes'));
const CandidatesPage = React.lazy(() => import('./pages/Candidates'));
const CandidateDetailPage = React.lazy(() => import('./pages/CandidateDetail'));
const SettingsPage = React.lazy(() => import('./pages/Settings'));

const ThemedApp: React.FC = () => {
  const { theme } = useAppSelector((state) => state.ui);
  const currentTheme = theme === 'dark' ? darkTheme : lightTheme;

  return (
    <ErrorBoundary>
      <ThemeProvider theme={currentTheme}>
        <CssBaseline />
        <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route
              path="jobs"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <JobsPage />
                </React.Suspense>
              }
            />
            <Route
              path="jobs/new"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <JobFormPage />
                </React.Suspense>
              }
            />
            <Route
              path="jobs/:id/edit"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <JobFormPage />
                </React.Suspense>
              }
            />
            <Route
              path="jobs/:id"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <JobDetailPage />
                </React.Suspense>
              }
            />
            <Route
              path="resumes"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <ResumesPage />
                </React.Suspense>
              }
            />
            <Route
              path="candidates"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <CandidatesPage />
                </React.Suspense>
              }
            />
            <Route
              path="candidates/:id"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <CandidateDetailPage />
                </React.Suspense>
              }
            />
            <Route
              path="settings"
              element={
                <React.Suspense fallback={<div>Loading...</div>}>
                  <SettingsPage />
                </React.Suspense>
              }
            />
          </Route>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </Router>
        <ToastContainer position="top-right" autoClose={3000} />
      </ThemeProvider>
    </ErrorBoundary>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ThemedApp />
    </Provider>
  );
};

export default App;
