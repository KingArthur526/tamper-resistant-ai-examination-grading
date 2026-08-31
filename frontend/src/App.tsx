import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ExamList } from './pages/ExamList';
import { CreateExamWizard } from './pages/CreateExamWizard';
import { AnswerSheetUpload } from './pages/AnswerSheetUpload';
import { OCRReview } from './pages/OCRReview';
import { ResultsWorkbench } from './pages/ResultsWorkbench';
import { ManualReviewQueue } from './pages/ManualReviewQueue';
import { AuditIntegrity } from './pages/AuditIntegrity';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  const [selectedExamId, setSelectedExamId] = useState<string>('');

  return (
    <BrowserRouter>
      <Layout selectedExamId={selectedExamId} onSelectExam={setSelectedExamId}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/exams" element={<ExamList />} />
          <Route path="/create-exam" element={<CreateExamWizard />} />
          <Route path="/answer-sheets" element={<AnswerSheetUpload />} />
          <Route path="/ocr-review" element={<OCRReview />} />
          <Route path="/results" element={<ResultsWorkbench />} />
          <Route path="/review-queue" element={<ManualReviewQueue />} />
          <Route path="/audit" element={<AuditIntegrity />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

export default App;
