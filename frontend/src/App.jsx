
import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout.jsx";
import { LoadingState } from "./components/Ui.jsx";
import AuthPage from "./auth/AuthPage.jsx";
import AuthGate from "./auth/AuthGate.jsx";
import { AuthProvider } from "./auth/AuthContext.jsx";

const AuditLogsPage = lazy(() => import("./pages/AuditLogsPage.jsx"));
const ItemsPage = lazy(() => import("./pages/ItemsPage.jsx"));
const LowStockPage = lazy(() => import("./pages/LowStockPage.jsx"));
const OverviewPage = lazy(() => import("./pages/OverviewPage.jsx"));
const ReportsPage = lazy(() => import("./pages/ReportsPage.jsx"));
const SettingsPage = lazy(() => import("./pages/SettingsPage.jsx"));
const StockManagementPage = lazy(() => import("./pages/StockManagementPage.jsx"));
const TransactionsPage = lazy(() => import("./pages/TransactionsPage.jsx"));

function page(element) {
  return (
    <Suspense fallback={<LoadingState label="Opening page..." />}>
      {element}
    </Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="login" element={<AuthPage mode="login" />} />
        <Route path="register" element={<AuthPage mode="register" />} />

        <Route
          element={
            <AuthGate>
              <AppLayout />
            </AuthGate>
          }
        >
          <Route index element={page(<OverviewPage />)} />
          <Route path="items" element={page(<ItemsPage />)} />
          <Route path="stock" element={page(<StockManagementPage />)} />
          <Route path="transactions" element={page(<TransactionsPage />)} />
          <Route path="low-stock" element={page(<LowStockPage />)} />
          <Route path="reports" element={page(<ReportsPage />)} />
          <Route path="audit-logs" element={page(<AuditLogsPage />)} />
          <Route path="settings" element={page(<SettingsPage />)} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}
