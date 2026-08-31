import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import (
    User, ExamSession, Question, RubricConcept, QuestionGroup,
    AnswerSheet, EvaluationConfig
)
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.integrity import calculate_sha256_file, calculate_sha256_text
from app.ml.ocr.engine import ocr_engine
from app.services.ocr_service import ocr_service
from app.services.grading_service import grading_service
from app.services.audit_service import log_audit_event

def seed_complete_demo(db: Session = None, user_id: str = None) -> str:
    close_db = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        # 1. Create or retrieve teacher user
        teacher = db.query(User).filter(User.email == "teacher@university.edu").first()
        if not teacher:
            teacher = User(
                email="teacher@university.edu",
                hashed_password=get_password_hash("admin123"),
                full_name="Prof. Alan Turing",
                role="teacher"
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)

        u_id = user_id or teacher.id

        # 2. Create Examination Session
        exam = ExamSession(
            name="End-Semester Examination - Computer Networks",
            subject="CS401 Computer Networks & Distributed Protocols",
            course_semester="B.Tech Computer Science - Semester 6",
            academic_year="2025-2026",
            exam_date=datetime.now().strftime("%Y-%m-%d"),
            description="Comprehensive descriptive examination covering OSI reference architecture, TCP protocol mechanics, and routing algorithms.",
            creator_id=u_id,
            total_marks=30.0,
            status="READY"
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        # Create evaluation configuration
        eval_cfg = EvaluationConfig(
            session_id=exam.id,
            model_name="all-MiniLM-L6-v2",
            full_match_threshold=0.78,
            partial_match_threshold=0.52,
            or_selection_policy="best_attempted",
            scoring_policy_version="v1.0-deterministic"
        )
        db.add(eval_cfg)
        db.commit()

        # 3. Create Questions & Rubric Concepts
        # Question 1: OSI Model (10 Marks)
        q1 = Question(
            session_id=exam.id,
            question_number="1",
            question_text="Explain the 7-layer architecture of the OSI Reference Model and detail the primary functions of the Physical, Data Link, Network, and Transport layers.",
            max_marks=10.0,
            question_type="DESCRIPTIVE"
        )
        db.add(q1)
        db.commit()
        db.refresh(q1)

        q1_concepts = [
            RubricConcept(
                question_id=q1.id,
                concept_code="C1.1",
                name="7-Layer Architecture Overview",
                description="General structural breakdown of the 7-layer OSI model.",
                reference_text="The OSI model is a 7-layer theoretical hierarchical architecture consisting of Physical, Data Link, Network, Transport, Session, Presentation, and Application layers.",
                max_marks=2.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["7 layers", "hierarchy", "OSI", "physical", "data link", "network", "transport"]
            ),
            RubricConcept(
                question_id=q1.id,
                concept_code="C1.2",
                name="Physical & Data Link Functions",
                description="Bit transmission, framing, and hardware MAC addressing.",
                reference_text="The Physical layer handles raw bit transmission over physical media, cables, and electrical signals. The Data Link layer provides framing, MAC hardware addressing, and local error detection.",
                max_marks=2.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["raw bits", "signals", "cables", "framing", "MAC address", "error detection"]
            ),
            RubricConcept(
                question_id=q1.id,
                concept_code="C1.3",
                name="Network Layer Routing & Addressing",
                description="Logical IP addressing and packet path determination.",
                reference_text="The Network layer is responsible for logical addressing (such as IP addresses) and packet routing across intermediate networks to determine optimal paths.",
                max_marks=2.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["IP address", "logical addressing", "routing", "packets", "paths"]
            ),
            RubricConcept(
                question_id=q1.id,
                concept_code="C1.4",
                name="Transport Layer End-to-End Reliability",
                description="Process-to-process delivery, segmentation, flow control, and error recovery.",
                reference_text="The Transport layer delivers end-to-end process-to-process communication, connection management, segmentation, flow control, and reliable delivery with acknowledgments.",
                max_marks=2.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["end-to-end", "flow control", "reliability", "acknowledgments", "segmentation"]
            ),
            RubricConcept(
                question_id=q1.id,
                concept_code="C1.5",
                name="Upper Layers (Session, Presentation, Application)",
                description="Dialog management, syntax/encryption, and user application interfaces.",
                reference_text="The Session layer manages dialogues, Presentation handles encryption and data translation, and Application provides network services to end-user software.",
                max_marks=2.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["session", "presentation", "encryption", "translation", "application"]
            )
        ]
        db.add_all(q1_concepts)
        db.commit()

        # Question 2: TCP 3-Way Handshake (10 Marks)
        q2 = Question(
            session_id=exam.id,
            question_number="2",
            question_text="Explain the TCP 3-way handshake mechanism for connection establishment and explain how TCP ensures reliable data transmission.",
            max_marks=10.0,
            question_type="DESCRIPTIVE"
        )
        db.add(q2)
        db.commit()
        db.refresh(q2)

        q2_concepts = [
            RubricConcept(
                question_id=q2.id,
                concept_code="C2.1",
                name="SYN Packet Transmission",
                description="Client sends SYN packet with Initial Sequence Number (ISN).",
                reference_text="The client initiates connection by sending a SYN packet containing an Initial Sequence Number (ISN) to the server to request a connection.",
                max_marks=2.5,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["SYN", "client", "ISN", "initial sequence number"]
            ),
            RubricConcept(
                question_id=q2.id,
                concept_code="C2.2",
                name="SYN-ACK Response",
                description="Server responds with SYN-ACK packet containing server ISN and acknowledgment of client sequence.",
                reference_text="The server responds with a SYN-ACK packet, acknowledging the client sequence number (ACK = ISN + 1) and providing its own sequence number.",
                max_marks=2.5,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["SYN-ACK", "acknowledgment", "server sequence"]
            ),
            RubricConcept(
                question_id=q2.id,
                concept_code="C2.3",
                name="ACK Final Handshake",
                description="Client sends final ACK to complete connection establishment.",
                reference_text="The client responds with an ACK packet acknowledging the server sequence, transitioning both endpoints to the ESTABLISHED state.",
                max_marks=2.5,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["ACK", "established state", "final acknowledgment"]
            ),
            RubricConcept(
                question_id=q2.id,
                concept_code="C2.4",
                name="TCP Reliability Guarantees",
                description="Sequence numbers, acknowledgments, checksums, and retransmissions.",
                reference_text="TCP guarantees reliability using sequence numbering, cumulative acknowledgments, checksum verification, and retransmission timers upon packet loss.",
                max_marks=2.5,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["cumulative ACK", "retransmission", "timers", "checksum", "packet loss"]
            )
        ]
        db.add_all(q2_concepts)
        db.commit()

        # Question 3: OR Group (10 Marks)
        q3_group = QuestionGroup(
            session_id=exam.id,
            name="Group 3 (Choice of Q3A or Q3B)",
            group_type="OR",
            selection_policy="best_attempted",
            max_selectable_marks=10.0
        )
        db.add(q3_group)
        db.commit()
        db.refresh(q3_group)

        # Question 3A
        q3a = Question(
            session_id=exam.id,
            group_id=q3_group.id,
            question_number="3A",
            question_text="Explain Distance Vector Routing, Bellman-Ford algorithm, and the Count-to-Infinity problem with solutions.",
            max_marks=10.0,
            question_type="OR_OPTION"
        )
        db.add(q3a)
        db.commit()
        db.refresh(q3a)

        q3a_concepts = [
            RubricConcept(
                question_id=q3a.id,
                concept_code="C3A.1",
                name="Distance Vector & Bellman-Ford",
                description="Periodic exchange of routing vectors with immediate neighbors.",
                reference_text="Distance Vector routing uses the Bellman-Ford algorithm where each router shares its full routing table vectors periodically only with adjacent neighbors.",
                max_marks=4.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["Distance Vector", "Bellman-Ford", "neighbors", "routing table"]
            ),
            RubricConcept(
                question_id=q3a.id,
                concept_code="C3A.2",
                name="Count-to-Infinity Problem",
                description="Routing loops causing metric to increment towards infinity during link failure.",
                reference_text="The Count-to-Infinity problem occurs when link failures cause routing loops, making routers continuously increment hop counts slowly toward infinity.",
                max_marks=3.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["Count to Infinity", "routing loop", "link failure", "slow convergence"]
            ),
            RubricConcept(
                question_id=q3a.id,
                concept_code="C3A.3",
                name="Mitigation Mechanisms",
                description="Split Horizon, Poison Reverse, and Hold-down timers.",
                reference_text="Count-to-Infinity is mitigated using Split Horizon (never advertise a route back on the interface it was learned), Poison Reverse (advertise cost infinity), and hold-down timers.",
                max_marks=3.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["Split Horizon", "Poison Reverse", "Hold-down timers"]
            )
        ]
        db.add_all(q3a_concepts)
        db.commit()

        # Question 3B
        q3b = Question(
            session_id=exam.id,
            group_id=q3_group.id,
            question_number="3B",
            question_text="Explain Link State Routing and Dijkstra's Shortest Path Algorithm.",
            max_marks=10.0,
            question_type="OR_OPTION"
        )
        db.add(q3b)
        db.commit()
        db.refresh(q3b)

        q3b_concepts = [
            RubricConcept(
                question_id=q3b.id,
                concept_code="C3B.1",
                name="Link State Advertisements & Flooding",
                description="Each node floods link state packets to all routers in topology.",
                reference_text="Link State routing broadcasts Link State Advertisements (LSAs) to all routers across the entire network to construct a global topology database.",
                max_marks=5.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["LSA", "flooding", "topology database", "global map"]
            ),
            RubricConcept(
                question_id=q3b.id,
                concept_code="C3B.2",
                name="Dijkstra Algorithm Calculation",
                description="Computing shortest path tree from source node.",
                reference_text="Each router independently runs Dijkstra's algorithm on its topology database to find the shortest path tree to all network destinations.",
                max_marks=5.0,
                full_match_threshold=0.78,
                partial_match_threshold=0.52,
                keywords=["Dijkstra", "shortest path tree", "SPF calculation"]
            )
        ]
        db.add_all(q3b_concepts)
        db.commit()

        # 4. Generate 6 Realistic Student Answer Sheets
        students_data = [
            {
                "id": "STU-101",
                "name": "Alice Smith",
                "roll": "CS2026-001",
                "answers": {
                    "1": (
                        "The OSI Reference Model is an open 7-layer theoretical network architecture. "
                        "The Physical layer transmits raw electrical bits and optical signals across physical cables and hardware interfaces. "
                        "The Data Link layer handles framing, MAC hardware addressing, and local error detection across the local hop. "
                        "The Network layer performs logical IP addressing and routing packets across intermediate networks to determine optimal paths. "
                        "The Transport layer provides reliable end-to-end communication between processes with segmentation, flow control, and acknowledgments. "
                        "The Session layer maintains session dialogues, Presentation handles syntax translation and encryption, and Application exposes user protocols."
                    ),
                    "2": (
                        "TCP establishes a connection using the 3-Way Handshake: "
                        "First, the client sends a SYN segment with an Initial Sequence Number (ISN). "
                        "Second, the server responds with a SYN-ACK segment, acknowledging the client sequence and sending its own server sequence. "
                        "Third, the client returns an ACK segment, moving the connection into the ESTABLISHED state. "
                        "TCP guarantees reliability using sequence numbering, cumulative acknowledgments, checksum verification, and retransmissions upon timeout."
                    ),
                    "3A": (
                        "Distance Vector routing is based on the Bellman-Ford algorithm where each router periodically exchanges its complete vector table with direct neighbors. "
                        "When a link fails, the Count-to-Infinity problem occurs where routing loops cause hop counts to increase gradually toward infinity. "
                        "This is resolved using Split Horizon where routes are not advertised back, Poison Reverse setting failed metric to infinity, and hold-down timers."
                    )
                }
            },
            {
                "id": "STU-102",
                "name": "Bob Johnson",
                "roll": "CS2026-002",
                "answers": {
                    "1": (
                        "OSI is divided into seven distinct conceptual layers from physical up to application. "
                        "Physical layer sends electrical pulses representing digital bits over copper wires or wireless media. "
                        "Data link handles frame encapsulation, switch MAC tables, and checksum validation. "
                        "Network layer handles logical routing using IP addresses to find paths across autonomous systems. "
                        "Transport provides process-to-process port delivery and flow control. "
                        "Upper layers handle data compression, encryption and application user interfaces."
                    ),
                    "2": (
                        "Connection starts with client transmitting SYN with initial sequence number. "
                        "Server replies with SYN+ACK acknowledging client and providing its number. "
                        "Final ACK completes handshake and connection is ready. "
                        "Reliability is achieved through retransmission timers, sequence numbers, and packet acknowledgments."
                    ),
                    "3A": (
                        "Distance vector utilizes Bellman-Ford calculation with periodic neighbor table broadcasts. "
                        "Count-to-infinity happens when broken links cause circulating updates incrementing hops. "
                        "Split horizon and poison reverse prevent loops by avoiding sending learned routes back."
                    )
                }
            },
            {
                "id": "STU-103",
                "name": "Charlie Brown",
                "roll": "CS2026-003",
                "answers": {
                    "1": (
                        "OSI model has 7 layers. "
                        "Physical layer is for cables and hardware. "
                        "Data link layer uses MAC addresses. "
                        "Network layer uses IP addresses and routers. "
                        "Transport layer sends data between computers."
                    ),
                    "2": (
                        "TCP 3-way handshake sends SYN from client to server, then server sends SYN-ACK back, then client sends ACK. "
                        "TCP is reliable because it sends acknowledgments."
                    ),
                    "3A": (
                        "Distance vector uses Bellman-Ford and routers talk to neighbors. "
                        "Count to infinity is a routing loop issue."
                    )
                }
            },
            {
                "id": "STU-104",
                "name": "Diana Prince",
                "roll": "CS2026-004",
                "answers": {
                    "1": (
                        "The network model connects computers. "
                        "The physical layer handles wires. "
                        "The transport layer provides routing with IP addresses. "
                        "Application layer runs software."
                    ),
                    "2": (
                        "TCP connects clients and servers by sending packets back and forth. "
                        "It uses handshakes and acknowledgments."
                    ),
                    "3A": (
                        "Routing algorithms find the shortest path between routers."
                    )
                }
            },
            {
                "id": "STU-105",
                "name": "Evan Wright",
                "roll": "CS2026-005",
                "answers": {
                    "1": (
                        "OSI Reference Model: 7 layers. Physical handles raw bits. "
                        "Data link handles MAC framing. Network layer uses IP routing. "
                        "Transport handles end to end delivery with acknowledgments."
                    ),
                    "2": (
                        "TCP handshake: Step 1 SYN, Step 2 SYN-ACK, Step 3 ACK. "
                        "Reliability with sequence numbers and retransmissions."
                    ),
                    "3B": (
                        "Link state routing broadcasts LSAs to all nodes. "
                        "Each node runs Dijkstra shortest path algorithm to build the routing tree."
                    )
                }
            },
            {
                "id": "STU-106",
                "name": "Fiona Gallagher",
                "roll": "CS2026-006",
                "answers": {
                    "1": (
                        "OSI 7 layers: Physical transmits raw bits and voltage. "
                        "Data link frames data and detects errors with MAC. "
                        "Network layer routes packets via IP. "
                        "Transport layer ensures end-to-end reliable transmission."
                    ),
                    "2": (
                        "TCP 3-way handshake: Client transmits SYN, Server replies with SYN-ACK, Client sends ACK. "
                        "Reliable transfer via cumulative ACKs and retransmissions."
                    ),
                    "3B": (
                        "Link State algorithm floods LSAs across the entire topology to create a database. "
                        "Then Dijkstra's algorithm computes the shortest path tree to all destinations."
                    )
                }
            }
        ]

        # Ingest and process all student answer sheets
        for s_info in students_data:
            # Build synthesized exam sheet text
            text_lines = [
                f"NAME: {s_info['name']} | ID: {s_info['id']} | ROLL: {s_info['roll']}",
                "=" * 65,
                ""
            ]
            for q_k, ans_v in s_info["answers"].items():
                text_lines.append(f"Question {q_k}:")
                text_lines.append(ans_v)
                text_lines.append("")

            # Render synthetic scanned handwriting image
            sample_img_path = settings.DEMO_SAMPLES_PATH / f"scan_{s_info['id']}.png"
            ocr_engine.render_handwritten_sample(
                text_lines=text_lines,
                output_path=sample_img_path,
                student_header=f"EXAMINATION SCRIPT - {s_info['name']} ({s_info['id']})"
            )

            # Also write OCR text file alongside
            transcript_file = sample_img_path.with_suffix(".txt")
            transcript_file.write_text("\n".join(text_lines), encoding="utf-8")

            # Copy to storage/original
            sha256 = calculate_sha256_file(sample_img_path)
            storage_path = settings.ORIGINAL_PATH / f"{sha256[:16]}_{s_info['id']}.png"
            shutil.copyfile(sample_img_path, storage_path)
            # Copy text transcript alongside
            shutil.copyfile(transcript_file, storage_path.with_suffix(".txt"))

            sheet = AnswerSheet(
                session_id=exam.id,
                student_id=s_info["id"],
                student_name=s_info["name"],
                roll_number=s_info["roll"],
                original_filename=f"AnswerSheet_{s_info['id']}.png",
                storage_path=str(storage_path),
                sha256_hash=sha256,
                file_size_bytes=storage_path.stat().st_size,
                processing_status="UPLOADED"
            )
            db.add(sheet)
            db.commit()
            db.refresh(sheet)

            log_audit_event(
                db=db,
                action="ANSWER_SHEET_UPLOADED",
                entity_type="AnswerSheet",
                entity_id=sheet.id,
                session_id=exam.id,
                user_id=u_id,
                payload={"student_id": sheet.student_id, "sha256": sha256}
            )

            # Process OCR
            ocr_service.process_answer_sheet_ocr(db, sheet.id, user_id=u_id)

            # Auto approve OCR for demo
            ocr_service.approve_ocr(db, sheet.id, user_id=u_id)

            # Run deterministic evaluation
            grading_service.evaluate_answer_sheet(db, sheet.id, user_id=u_id)

        exam.status = "COMPLETED"
        db.commit()

        log_audit_event(
            db=db,
            action="DEMO_EXAM_SEEDED_AND_EVALUATED",
            entity_type="ExamSession",
            entity_id=exam.id,
            session_id=exam.id,
            user_id=u_id,
            payload={"exam_name": exam.name, "students_count": len(students_data)}
        )

        print(f"Demo Exam Seeded Successfully! Exam ID: {exam.id}")
        return exam.id

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_complete_demo()
