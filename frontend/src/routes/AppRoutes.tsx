import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { AuthLayout } from '../layouts/AuthLayout';
import { LoginPage } from '../pages/auth/LoginPage';
import { SignupPage } from '../pages/auth/SignupPage';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { RiskRankingPage } from '../pages/ranking/RiskRankingPage';
import { ProjectDetailPage } from '../pages/project/ProjectDetailPage';
import { ProjectDriversPage } from '../pages/project/ProjectDriversPage';
import { ProjectInterventionsPage } from '../pages/project/ProjectInterventionsPage';
import { NotFoundPage } from '../pages/NotFoundPage';

/**
 * PAIMANA Canonical Application Routes
 * Strictly adheres to the 5 authoritative screens + authentication foundation.
 */
export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Authentication Flow */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Route>

      {/* Main PAIMANA Application Shell */}
      <Route element={<AppShell />}>
        {/* Root Redirect to Dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* 1. Portfolio Overview Dashboard */}
        <Route path="/dashboard" element={<DashboardPage />} />

        {/* 2. Risk Ranking Leaderboard */}
        <Route path="/risk-ranking" element={<RiskRankingPage />} />

        {/* 3. Project Detail Profile */}
        <Route path="/projects/:canonicalProjectKey" element={<ProjectDetailPage />} />

        {/* 4. Explainable Risk Drivers */}
        <Route path="/projects/:canonicalProjectKey/drivers" element={<ProjectDriversPage />} />

        {/* 5. Intervention Action Panel */}
        <Route path="/projects/:canonicalProjectKey/interventions" element={<ProjectInterventionsPage />} />

        {/* Fallback 404 Route */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
