export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface RubricConcept {
  id: string;
  concept_code: string;
  name: string;
  description?: string;
  reference_text: string;
  max_marks: number;
  required: boolean;
  full_match_threshold: number;
  partial_match_threshold: number;
  keywords?: string[];
  negative_indicators?: string[];
  weight: number;
}

export interface QuestionGroup {
  id: string;
  session_id: string;
  name: string;
  group_type: string;
  selection_policy: string;
  max_selectable_marks: number;
}

export interface Question {
  id: string;
  session_id: string;
  group_id?: string;
  question_number: string;
  question_text: string;
  max_marks: number;
  question_type: string;
  instructions?: string;
  rubric_version: number;
  rubric_concepts: RubricConcept[];
}

export interface ExamSession {
  id: string;
  name: string;
  subject: string;
  course_semester: string;
  academic_year: string;
  exam_date: string;
  description?: string;
  total_marks: number;
  status: string;
  is_finalized: boolean;
  created_at: string;
  updated_at: string;
  questions?: Question[];
  question_groups?: QuestionGroup[];
  total_answer_sheets?: number;
  evaluated_count?: number;
  average_score?: number;
}

export interface DashboardStats {
  total_exams: number;
  active_exams: number;
  completed_evaluations: number;
  pending_evaluations: number;
  total_answer_sheets: number;
  average_marks_percentage: number;
  recent_exams: ExamSession[];
}

export interface AnswerSheet {
  id: string;
  session_id: string;
  student_id: string;
  student_name: string;
  roll_number?: string;
  original_filename: string;
  sha256_hash: string;
  preprocessed_hash?: string;
  ocr_hash?: string;
  processing_status: string;
  ocr_confidence_avg: number;
  error_message?: string;
  uploaded_at: string;
  total_score?: number;
  max_marks?: number;
  percentage?: number;
  needs_review: boolean;
}

export interface StudentAnswerDetail {
  id: string;
  question_id: string;
  question_number: string;
  question_text: string;
  max_marks: number;
  raw_ocr_text: string;
  cleaned_text: string;
  teacher_edited_text?: string;
  is_edited: boolean;
  ocr_confidence: number;
  segmentation_confidence: number;
  attempted: boolean;
}

export interface AnswerSheetPage {
  page_number: number;
  sheet_id: string;
  image_url: string;
  preprocessed_image_url?: string;
  filename: string;
  sha256_hash: string;
}

export interface OCRReviewData {
  answer_sheet_id: string;
  student_id: string;
  student_name: string;
  original_filename: string;
  sha256_hash: string;
  original_image_url: string;
  preprocessed_image_url?: string;
  ocr_confidence_avg: number;
  status: string;
  pages?: AnswerSheetPage[];
  raw_entire_sheet_text?: string;
  answers: StudentAnswerDetail[];
}

export interface ConceptEvaluation {
  id: string;
  rubric_concept_id: string;
  concept_code: string;
  concept_name: string;
  concept_description?: string;
  reference_text: string;
  similarity_score: number;
  semantic_status: 'FULL_MATCH' | 'PARTIAL_MATCH' | 'MISSING';
  awarded_marks: number;
  max_marks: number;
  matched_evidence?: string;
  matched_span_indices?: number[];
  missing_evidence: string[];
  explanation: string;
  confidence_score: number;
  model_name: string;
  scoring_policy: string;
}

export interface SpellingErrorItem {
  word: string;
  suggested_correction: string;
  context: string;
}

export interface QuestionEvaluation {
  id: string;
  answer_sheet_id: string;
  question_id: string;
  question_number: string;
  question_text: string;
  max_marks: number;
  student_answer_text: string;
  ocr_confidence: number;
  ai_score: number;
  teacher_final_score: number;
  is_overridden: boolean;
  confidence_level: string;
  needs_review: boolean;
  review_reasons: string[];
  calculation_trace: any;
  is_or_group_selected: boolean;
  spelling_score?: number;
  spelling_penalty_deducted?: number;
  spelling_errors?: SpellingErrorItem[];
  status: string;
  concept_evaluations: ConceptEvaluation[];
}

export interface StudentResultCard {
  answer_sheet_id: string;
  student_id: string;
  student_name: string;
  roll_number?: string;
  session_id: string;
  session_name: string;
  subject: string;
  total_ai_score: number;
  total_teacher_score: number;
  total_max_marks: number;
  percentage: number;
  integrity_hash: string;
  status: string;
  needs_review: boolean;
  is_finalized: boolean;
  questions: QuestionEvaluation[];
}

export interface WhyThisScoreData {
  question_evaluation_id: string;
  question_number: string;
  question_text: string;
  question_max_marks: number;
  ai_score: number;
  teacher_final_score: number;
  is_overridden: boolean;
  confidence_level: string;
  ocr_confidence: number;
  semantic_model: string;
  similarity_method: string;
  scoring_policy: string;
  spelling_score?: number;
  spelling_penalty_deducted?: number;
  spelling_errors?: SpellingErrorItem[];
  concepts: ConceptEvaluation[];
  calculation_formula: string;
  calculation_breakdown: Array<{
    concept_code: string;
    concept_name: string;
    max_marks: number;
    awarded_marks: number;
    similarity_score: number;
    status: string;
    matched_evidence?: string;
    missing_evidence: string[];
    explanation: string;
  }>;
  evaluation_hash?: string;
  timestamp: string;
}

export interface AuditLog {
  id: string;
  session_id?: string;
  user_id?: string;
  user_name?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  payload: any;
  previous_hash: string;
  event_hash: string;
  timestamp: string;
  is_tampered: boolean;
}

export interface IntegrityVerificationResult {
  session_id: string;
  overall_status: 'VERIFIED' | 'COMPROMISED';
  total_files_checked: number;
  files_valid: number;
  files_tampered: number;
  tampered_files_detail: any[];
  total_audit_events: number;
  audit_chain_valid: boolean;
  broken_chain_indices: number[];
  checked_at: string;
}

export interface EvaluationConfig {
  id: string;
  session_id: string;
  model_name: string;
  embedding_dim: number;
  similarity_metric: string;
  full_match_threshold: number;
  partial_match_threshold: number;
  or_selection_policy: string;
  scoring_policy_version: string;
}
