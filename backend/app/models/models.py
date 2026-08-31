from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="teacher", nullable=False) # teacher, admin, evaluator
    created_at = Column(DateTime, default=utc_now, nullable=False)

    exam_sessions = relationship("ExamSession", back_populates="creator")
    teacher_overrides = relationship("TeacherOverride", back_populates="teacher")
    audit_logs = relationship("AuditLog", back_populates="user")


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    course_semester = Column(String(100), nullable=False)
    academic_year = Column(String(50), nullable=False)
    exam_date = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    total_marks = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False) # DRAFT, READY, EVALUATING, COMPLETED, FINALIZED
    is_finalized = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    creator = relationship("User", back_populates="exam_sessions")
    question_groups = relationship("QuestionGroup", back_populates="session", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan", order_by="Question.question_number")
    answer_sheets = relationship("AnswerSheet", back_populates="session", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="session", cascade="all, delete-orphan")
    evaluation_configs = relationship("EvaluationConfig", back_populates="session", cascade="all, delete-orphan")


class QuestionGroup(Base):
    """Represents an OR-group of questions where a subset must be selected."""
    __tablename__ = "question_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False) # e.g. "Group 5 (Q5A or Q5B)"
    group_type = Column(String(50), default="OR", nullable=False) # OR, MANDATORY
    selection_policy = Column(String(50), default="best_attempted", nullable=False) # best_attempted, first_attempted
    max_selectable_marks = Column(Float, nullable=False) # Max marks this group contributes

    session = relationship("ExamSession", back_populates="question_groups")
    questions = relationship("Question", back_populates="group")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(36), ForeignKey("question_groups.id", ondelete="SET NULL"), nullable=True)
    question_number = Column(String(50), nullable=False) # e.g. "1", "2(a)", "5A"
    question_text = Column(Text, nullable=False)
    max_marks = Column(Float, nullable=False)
    question_type = Column(String(50), default="DESCRIPTIVE", nullable=False) # DESCRIPTIVE, OR_OPTION
    instructions = Column(Text, nullable=True)
    rubric_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("ExamSession", back_populates="questions")
    group = relationship("QuestionGroup", back_populates="questions")
    rubric_concepts = relationship("RubricConcept", back_populates="question", cascade="all, delete-orphan", order_by="RubricConcept.concept_code")
    student_answers = relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")
    question_evaluations = relationship("QuestionEvaluation", back_populates="question", cascade="all, delete-orphan")


class RubricConcept(Base):
    __tablename__ = "rubric_concepts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    concept_code = Column(String(50), nullable=False) # e.g. "C1", "C2"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reference_text = Column(Text, nullable=False) # The expected explanation / canonical reference
    max_marks = Column(Float, nullable=False)
    required = Column(Boolean, default=True, nullable=False)
    full_match_threshold = Column(Float, default=0.78, nullable=False)
    partial_match_threshold = Column(Float, default=0.52, nullable=False)
    keywords = Column(JSON, default=list, nullable=False) # Optional list of key terms/synonyms
    negative_indicators = Column(JSON, default=list, nullable=False) # Optional misconceptions
    weight = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    question = relationship("Question", back_populates="rubric_concepts")
    concept_evaluations = relationship("ConceptEvaluation", back_populates="rubric_concept", cascade="all, delete-orphan")


class AnswerSheet(Base):
    __tablename__ = "answer_sheets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(100), index=True, nullable=False)
    student_name = Column(String(255), nullable=False)
    roll_number = Column(String(100), nullable=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False) # Immutable original file path
    preprocessed_path = Column(String(500), nullable=True) # Preprocessed image path
    ocr_raw_path = Column(String(500), nullable=True) # Stored raw OCR transcript
    sha256_hash = Column(String(64), nullable=False) # Original file SHA-256
    preprocessed_hash = Column(String(64), nullable=True) # Preprocessed file SHA-256
    ocr_hash = Column(String(64), nullable=True) # OCR text SHA-256
    file_size_bytes = Column(Integer, default=0, nullable=False)
    processing_status = Column(String(50), default="UPLOADED", nullable=False)
    # Statuses: UPLOADED, PREPROCESSING, OCR_COMPLETED, NEEDS_OCR_REVIEW, OCR_APPROVED, EVALUATING, EVALUATED, FINALIZED, ERROR
    ocr_confidence_avg = Column(Float, default=0.0, nullable=False)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    ocr_completed_at = Column(DateTime, nullable=True)

    session = relationship("ExamSession", back_populates="answer_sheets")
    student_answers = relationship("StudentAnswer", back_populates="answer_sheet", cascade="all, delete-orphan")
    question_evaluations = relationship("QuestionEvaluation", back_populates="answer_sheet", cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    answer_sheet_id = Column(String(36), ForeignKey("answer_sheets.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    raw_ocr_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    teacher_edited_text = Column(Text, nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    ocr_confidence = Column(Float, default=1.0, nullable=False)
    segmentation_confidence = Column(Float, default=1.0, nullable=False)
    bounding_boxes = Column(JSON, default=list, nullable=False) # Visual bounding boxes from scan
    attempted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    answer_sheet = relationship("AnswerSheet", back_populates="student_answers")
    question = relationship("Question", back_populates="student_answers")
    concept_evaluations = relationship("ConceptEvaluation", back_populates="student_answer", cascade="all, delete-orphan")


class ConceptEvaluation(Base):
    __tablename__ = "concept_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_answer_id = Column(String(36), ForeignKey("student_answers.id", ondelete="CASCADE"), nullable=False)
    rubric_concept_id = Column(String(36), ForeignKey("rubric_concepts.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=False) # Dense cosine similarity
    semantic_status = Column(String(50), nullable=False) # FULL_MATCH, PARTIAL_MATCH, MISSING
    awarded_marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    matched_evidence = Column(Text, nullable=True) # Exact verbatim student sentence/span
    matched_span_indices = Column(JSON, default=list, nullable=False) # [start_char, end_char]
    missing_evidence = Column(JSON, default=list, nullable=False) # List of missing aspects/components
    explanation = Column(Text, nullable=False) # Grounded factual rationale
    confidence_score = Column(Float, default=1.0, nullable=False)
    model_name = Column(String(100), nullable=False)
    scoring_policy = Column(String(100), nullable=False)
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    student_answer = relationship("StudentAnswer", back_populates="concept_evaluations")
    rubric_concept = relationship("RubricConcept", back_populates="concept_evaluations")


class QuestionEvaluation(Base):
    __tablename__ = "question_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    answer_sheet_id = Column(String(36), ForeignKey("answer_sheets.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    ai_score = Column(Float, default=0.0, nullable=False)
    teacher_final_score = Column(Float, default=0.0, nullable=False)
    is_overridden = Column(Boolean, default=False, nullable=False)
    confidence_level = Column(String(50), default="HIGH", nullable=False) # HIGH, MEDIUM, LOW, MANUAL_REVIEW_REQUIRED
    needs_review = Column(Boolean, default=False, nullable=False)
    review_reasons = Column(JSON, default=list, nullable=False)
    calculation_trace = Column(JSON, default=dict, nullable=False) # {concept_scores: [...], sum_formula: "2 + 1 = 3", max_marks: 10}
    is_or_group_selected = Column(Boolean, default=True, nullable=False)
    spelling_score = Column(Float, default=100.0, nullable=False) # Spelling accuracy percentage (0-100%)
    spelling_penalty_deducted = Column(Float, default=0.0, nullable=False) # Bounded mark deduction
    spelling_errors = Column(JSON, default=list, nullable=False) # [{"word": "...", "suggested_correction": "...", "context": "..."}]
    evaluation_version = Column(Integer, default=1, nullable=False)
    evaluation_hash = Column(String(64), nullable=True)
    status = Column(String(50), default="EVALUATED", nullable=False) # EVALUATED, OVERRIDDEN, FINALIZED
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    answer_sheet = relationship("AnswerSheet", back_populates="question_evaluations")
    question = relationship("Question", back_populates="question_evaluations")
    overrides = relationship("TeacherOverride", back_populates="question_evaluation", cascade="all, delete-orphan", order_by="desc(TeacherOverride.timestamp)")


class TeacherOverride(Base):
    __tablename__ = "teacher_overrides"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_evaluation_id = Column(String(36), ForeignKey("question_evaluations.id", ondelete="CASCADE"), nullable=False)
    previous_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    override_reason = Column(Text, nullable=False)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    teacher_name = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    audit_event_id = Column(String(36), nullable=True)

    question_evaluation = relationship("QuestionEvaluation", back_populates="overrides")
    teacher = relationship("User", back_populates="teacher_overrides")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=True)
    payload = Column(JSON, default=dict, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    is_tampered = Column(Boolean, default=False, nullable=False)

    session = relationship("ExamSession", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")


class EvaluationConfig(Base):
    __tablename__ = "evaluation_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), default="all-MiniLM-L6-v2", nullable=False)
    embedding_dim = Column(Integer, default=384, nullable=False)
    similarity_metric = Column(String(50), default="Cosine Similarity", nullable=False)
    full_match_threshold = Column(Float, default=0.78, nullable=False)
    partial_match_threshold = Column(Float, default=0.52, nullable=False)
    or_selection_policy = Column(String(50), default="best_attempted", nullable=False)
    enable_spelling_evaluation = Column(Boolean, default=True, nullable=False)
    spelling_deduction_per_error = Column(Float, default=0.25, nullable=False)
    spelling_max_penalty = Column(Float, default=1.0, nullable=False)
    scoring_policy_version = Column(String(50), default="v1.0-deterministic", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("ExamSession", back_populates="evaluation_configs")
