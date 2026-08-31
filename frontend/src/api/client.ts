const API_BASE = '/api';

export const api = {
  // Auth
  login: async (credentials: any) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getMe: async () => {
    const res = await fetch(`${API_BASE}/auth/me`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Dashboard & Exams
  getDashboardStats: async () => {
    const res = await fetch(`${API_BASE}/exams/dashboard-stats`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  listExams: async () => {
    const res = await fetch(`${API_BASE}/exams`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getExam: async (id: string) => {
    const res = await fetch(`${API_BASE}/exams/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  createExam: async (data: any) => {
    const res = await fetch(`${API_BASE}/exams`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  deleteExam: async (id: string) => {
    const res = await fetch(`${API_BASE}/exams/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Questions & Rubrics
  getExamQuestions: async (examId: string) => {
    const res = await fetch(`${API_BASE}/questions/exam/${examId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  addQuestion: async (examId: string, data: any) => {
    const res = await fetch(`${API_BASE}/questions/exam/${examId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  validateRubric: async (maxMarks: number, concepts: any[]) => {
    const res = await fetch(`${API_BASE}/questions/validate-rubric?question_max_marks=${maxMarks}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(concepts)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Answer Sheets & Upload
  getExamAnswerSheets: async (examId: string) => {
    const res = await fetch(`${API_BASE}/answer-sheets/exam/${examId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  uploadAnswerSheet: async (examId: string, formData: FormData) => {
    const res = await fetch(`${API_BASE}/answer-sheets/upload/${examId}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // OCR
  processOCR: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/ocr/process/${sheetId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  processAllOCR: async (examId: string) => {
    const res = await fetch(`${API_BASE}/ocr/process-all/${examId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getOCRReview: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/ocr/review/${sheetId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  submitOCRCorrections: async (sheetId: string, corrections: any[], reEvaluate: boolean = true) => {
    const res = await fetch(`${API_BASE}/ocr/correct/${sheetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrections, re_evaluate: reEvaluate })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  submitEntireRawOCR: async (sheetId: string, entireText: string, reEvaluate: boolean = true) => {
    const res = await fetch(`${API_BASE}/ocr/correct-entire-raw/${sheetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entire_text: entireText, re_evaluate: reEvaluate })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  approveOCR: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/ocr/approve/${sheetId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Evaluation & Results
  evaluateSheet: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/evaluations/run/${sheetId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  evaluateExam: async (examId: string) => {
    const res = await fetch(`${API_BASE}/evaluations/run-exam/${examId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getStudentResults: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/evaluations/student-results/${sheetId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getWhyThisScore: async (questionEvalId: string) => {
    const res = await fetch(`${API_BASE}/evaluations/why-this-score/${questionEvalId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  getNeedsReviewQueue: async (examId: string) => {
    const res = await fetch(`${API_BASE}/evaluations/needs-review-queue/${examId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Overrides
  applyOverride: async (questionEvalId: string, data: { new_score: number; override_reason: string }) => {
    const res = await fetch(`${API_BASE}/overrides/${questionEvalId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Audit & Integrity
  getAuditLogs: async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/audit/logs/${sessionId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  verifyIntegrity: async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/audit/verify-integrity/${sessionId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  simulateTamper: async (sheetId: string) => {
    const res = await fetch(`${API_BASE}/audit/simulate-tamper/${sheetId}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Settings
  getConfig: async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/settings/${sessionId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  updateConfig: async (sessionId: string, data: any) => {
    const res = await fetch(`${API_BASE}/settings/${sessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Demo Seed
  seedDemo: async () => {
    const res = await fetch(`${API_BASE}/demo/seed`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
