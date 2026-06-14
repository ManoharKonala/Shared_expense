import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import GroupPage from './pages/GroupPage';
import ExpenseDetailPage from './pages/ExpenseDetailPage';
import ImportPage from './pages/ImportPage';
import AuditLogPage from './pages/AuditLogPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout>
            <DashboardPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/groups/:groupId" element={
        <ProtectedRoute>
          <Layout>
            <GroupPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/expenses/:expenseId" element={
        <ProtectedRoute>
          <Layout>
            <ExpenseDetailPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/groups/:groupId/import" element={
        <ProtectedRoute>
          <Layout>
            <ImportPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/audit" element={
        <ProtectedRoute>
          <Layout>
            <AuditLogPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
