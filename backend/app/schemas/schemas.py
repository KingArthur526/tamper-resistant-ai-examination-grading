from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# --- Auth ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "teacher"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Rubric Concepts ---
class RubricConceptBase(BaseModel):
    concept_code: str = Field(..., example="C1")
    name: str = Field(..., example="Seven-layer hierarchy")
    description: Optional[str] = None
    reference_text: str = Field(..., example="The OSI model is a 7-layer theoretical network architecture.")
    max_marks: float = Field(..., gt=0, example=2.0)
    required: bool = True
    full_match_threshold: float = Field(0.78, ge=0.0, le=1.0)
    partial_match_threshold: float = Field(0.52, ge=0.0, le=1.0)
    keywords: List[str] = []
    negative_indicators: List[str] = []
    weight: float = 1.0

class RubricConceptCreate(RubricConceptBase):
    pass

class RubricConceptUpdate(BaseModel):
    concept_code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    reference_text: Optional[str] = None
    max_marks: Optional[float] = None
    required: Optional[bool] = None
    full_match_threshold: Optional[float] = None
    partial_match_threshold: Optional[float] = None
    keywords: Optional[List[str]] = None
    negative_indicators: Optional[List[str]] = None
    weight: Optional[float] = None

class RubricConceptResponse(RubricConceptBase):
    id: str
    question_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Question Groups (OR-groups) ---
class QuestionGroupCreate(BaseModel):
    name: str = Field(..., example="Group 5 (Q5A or Q5B)")
    group_type: str = "OR"
    selection_policy: str = "best_attempted"
    max_selectable_marks: float = Field(..., gt=0, example=10.0)

class QuestionGroupResponse(BaseModel):
    id: str
    session_id: str
    name: str
    group_type: str
    selection_policy: str
    max_selectable_marks: float

    class Config:
        from_attributes = True

# --- Questions ---
class QuestionCreate(BaseModel):
    question_number: str = Field(..., example="1")
    question_text: str = Field(..., example="Explain the architecture and key responsibilities of the OSI 7-layer model.")
    max_marks: float = Field(..., gt=0, example=10.0)
    question_type: str = "DESCRIPTIVE" # DESCRIPTIVE or OR_OPTION
    group_id: Optional[str] = None
    instructions: Optional[str] = None
    rubric_concepts: List[RubricConceptCreate] = []

class QuestionUpdate(BaseModel):
    question_number: Optional[str] = None
    question_text: Optional[str] = None
    max_marks: Optional[float] = None
    question_type: Optional[str] = None
    group_id: Optional[str] = None
    instructions: Optional[str] = None

class QuestionResponse(BaseModel):
    id: str
    session_id: str
    group_id: Optional[str] = None
    question_number: str
    question_text: str
    max_marks: float
    question_type: str
    instructions: Optional[str] = None
    rubric_version: int
    created_at: datetime
    rubric_concepts: List[RubricConceptResponse] = []

    class Config:
        from_attributes = True

class RubricValidationResponse(BaseModel):
    is_valid: bool
    question_number: str
    question_max_marks: float
    concepts_total_marks: float
    difference: float
    message: str

# --- Exam Sessions ---
class ExamSessionCreate(BaseModel):
    name: str = Field(..., example="End-Semester Examination - Computer Networks")
    subject: str = Field(..., example="CS401 Computer Networks")
    course_semester: str = Field(..., example="B.Tech CS - Sem 6")
    academic_year: str = Field(..., example="2025-2026")
    exam_date: str = Field(..., example="2026-05-15")
    description: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None

class ExamSessionUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    course_semester: Optional[str] = None
    academic_year: Optional[str] = None
    exam_date: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ExamSessionResponse(BaseModel):
    id: str
    name: str
    subject: str
    course_semester: str
    academic_year: str
    exam_date: str
    description: Optional[str] = None
    total_marks: float
    status: str
    is_finalized: bool
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []
    question_groups: List[QuestionGroupResponse] = []
    total_answer_sheets: int = 0
    evaluated_count: int = 0
    average_score: Optional[float] = None

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_exams: int
    active_exams: int
    completed_evaluations: int
    pending_evaluations: int
    total_answer_sheets: int
    average_marks_percentage: float
    recent_exams: List[ExamSessionResponse] = []

# --- Answer Sheets & OCR ---
class AnswerSheetResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    original_filename: str
    sha256_hash: str
    preprocessed_hash: Optional[str] = None
    ocr_hash: Optional[str] = None
    processing_status: str
    ocr_confidence_avg: float
    error_message: Optional[str] = None
    uploaded_at: datetime
    ocr_completed_at: Optional[datetime] = None
    total_score: Optional[float] = None
    max_marks: Optional[float] = None
    percentage: Optional[float] = None
    needs_review: bool = False

    class Config:
        from_attributes = True

class StudentAnswerDetail(BaseModel):
    id: str
    question_id: str
    question_number: str
    question_text: str
    max_marks: float
    raw_ocr_text: str
    cleaned_text: str
    teacher_edited_text: Optional[str] = None
    is_edited: bool
    ocr_confidence: float
    segmentation_confidence: float
    attempted: bool

    class Config:
        from_attributes = True

class AnswerSheetPage(BaseModel):
    page_number: int
    sheet_id: str
    image_url: str
    preprocessed_image_url: Optional[str] = None
    filename: str
    sha256_hash: str

class OCRReviewResponse(BaseModel):
    answer_sheet_id: str
    student_id: str
    student_name: str
    original_filename: str
    sha256_hash: str
    original_image_url: str
    preprocessed_image_url: Optional[str] = None
    ocr_confidence_avg: float
    status: str
    pages: List[AnswerSheetPage] = []
    raw_entire_sheet_text: Optional[str] = None
    answers: List[StudentAnswerDetail] = []

class OCRCorrectionItem(BaseModel):
    student_answer_id: str
    edited_text: str
    attempted: bool = True

class OCRCorrectionRequest(BaseModel):
    corrections: List[OCRCorrectionItem]
    re_evaluate: bool = True

class EntireSheetCorrectionRequest(BaseModel):
    entire_text: Optional[str] = None
    corrections: Optional[List[OCRCorrectionItem]] = None
    re_evaluate: bool = True

# --- Evaluation & Why-This-Score ---
class ConceptEvaluationResponse(BaseModel):
    id: str
    rubric_concept_id: str
    concept_code: str
    concept_name: str
    concept_description: Optional[str] = None
    reference_text: str
    similarity_score: float
    semantic_status: str # FULL_MATCH, PARTIAL_MATCH, MISSING
    awarded_marks: float
    max_marks: float
    matched_evidence: Optional[str] = None
    matched_span_indices: List[int] = []
    missing_evidence: List[str] = []
    explanation: str
    confidence_score: float
    model_name: str
    scoring_policy: str

class QuestionEvaluationResponse(BaseModel):
    id: str
    answer_sheet_id: str
    question_id: str
    question_number: str
    question_text: str
    max_marks: float
    student_answer_text: str
    ocr_confidence: float
    ai_score: float
    teacher_final_score: float
    is_overridden: bool
    confidence_level: str
    needs_review: bool
    review_reasons: List[str] = []
    calculation_trace: Dict[str, Any] = {}
    is_or_group_selected: bool
    spelling_score: float = 100.0
    spelling_penalty_deducted: float = 0.0
    spelling_errors: List[Dict[str, Any]] = []
    status: str
    concept_evaluations: List[ConceptEvaluationResponse] = []

    class Config:
        from_attributes = True

class WhyThisScoreResponse(BaseModel):
    question_evaluation_id: str
    question_number: str
    question_text: str
    question_max_marks: float
    ai_score: float
    teacher_final_score: float
    is_overridden: bool
    confidence_level: str
    ocr_confidence: float
    semantic_model: str
    similarity_method: str
    scoring_policy: str
    spelling_score: float = 100.0
    spelling_penalty_deducted: float = 0.0
    spelling_errors: List[Dict[str, Any]] = []
    concepts: List[ConceptEvaluationResponse] = []
    calculation_formula: str
    calculation_breakdown: List[Dict[str, Any]] = []
    evaluation_hash: Optional[str] = None
    timestamp: datetime

class StudentResultCard(BaseModel):
    answer_sheet_id: str
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    session_id: str
    session_name: str
    subject: str
    total_ai_score: float
    total_teacher_score: float
    total_max_marks: float
    percentage: float
    integrity_hash: str
    status: str
    needs_review: bool
    is_finalized: bool
    questions: List[QuestionEvaluationResponse] = []

# --- Teacher Override ---
class TeacherOverrideRequest(BaseModel):
    new_score: float = Field(..., ge=0)
    override_reason: str = Field(..., min_length=5, example="Student used alternative correct notation for subnet masks.")

class TeacherOverrideResponse(BaseModel):
    id: str
    question_evaluation_id: str
    previous_score: float
    new_score: float
    override_reason: str
    teacher_name: str
    timestamp: datetime

# --- Tamper & Audit Trail ---
class AuditLogResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    payload: Dict[str, Any] = {}
    previous_hash: str
    event_hash: str
    timestamp: datetime
    is_tampered: bool = False

    class Config:
        from_attributes = True

class IntegrityVerificationResponse(BaseModel):
    session_id: str
    overall_status: str # VERIFIED, COMPROMISED
    total_files_checked: int
    files_valid: int
    files_tampered: int
    tampered_files_detail: List[Dict[str, Any]] = []
    total_audit_events: int
    audit_chain_valid: bool
    broken_chain_indices: List[int] = []
    checked_at: datetime

# --- Evaluation Config ---
class EvaluationConfigResponse(BaseModel):
    id: str
    session_id: str
    model_name: str
    embedding_dim: int
    similarity_metric: str
    full_match_threshold: float
    partial_match_threshold: float
    or_selection_policy: str
    scoring_policy_version: str

    class Config:
        from_attributes = True

class EvaluationConfigUpdate(BaseModel):
    model_name: Optional[str] = None
    full_match_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    partial_match_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    or_selection_policy: Optional[str] = None
