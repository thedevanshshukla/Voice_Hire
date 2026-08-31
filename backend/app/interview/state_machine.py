import time
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.models.interview import InterviewStage, InterviewConfig
from app.core.logger import get_logger

logger = get_logger("interview.state_machine")

STAGE_SEQUENCE: List[InterviewStage] = [
    InterviewStage.GREETING,
    InterviewStage.RESUME_DEEP_DIVE,
    InterviewStage.CORE_CONCEPTS,
    InterviewStage.SYSTEM_DESIGN,
    InterviewStage.CANDIDATE_QUESTIONS,
    InterviewStage.WRAP_UP
]

STAGE_DISPLAY_NAMES: Dict[InterviewStage, str] = {
    InterviewStage.GREETING: "Introduction & Warm-Up",
    InterviewStage.RESUME_DEEP_DIVE: "Past Projects & Experience",
    InterviewStage.CORE_CONCEPTS: "Core Technical Concepts",
    InterviewStage.SYSTEM_DESIGN: "System Architecture & Design",
    InterviewStage.CANDIDATE_QUESTIONS: "Candidate Q&A",
    InterviewStage.WRAP_UP: "Wrap-Up & Debrief"
}

# Proportional time percentages
STAGE_PERCENTAGES: Dict[InterviewStage, float] = {
    InterviewStage.GREETING: 0.10,
    InterviewStage.RESUME_DEEP_DIVE: 0.20,
    InterviewStage.CORE_CONCEPTS: 0.35,
    InterviewStage.SYSTEM_DESIGN: 0.25,
    InterviewStage.CANDIDATE_QUESTIONS: 0.07,
    InterviewStage.WRAP_UP: 0.03
}

# Min and max turn guidelines per stage
STAGE_TURN_BUDGETS: Dict[InterviewStage, Tuple[int, int]] = {
    InterviewStage.GREETING: (1, 2),
    InterviewStage.RESUME_DEEP_DIVE: (2, 3),
    InterviewStage.CORE_CONCEPTS: (3, 5),
    InterviewStage.SYSTEM_DESIGN: (2, 4),
    InterviewStage.CANDIDATE_QUESTIONS: (1, 2),
    InterviewStage.WRAP_UP: (1, 1)
}

class StageBudget(BaseModel):
    stage: InterviewStage
    display_name: str
    target_duration_minutes: float
    min_turns: int
    max_turns: int

class StageTransitionResult(BaseModel):
    transitioned: bool
    previous_stage: InterviewStage
    current_stage: InterviewStage
    stage_display_name: str
    progress_pct: float
    stage_directive: str

class InterviewStateMachine:
    """
    Finite State Machine orchestrating multi-stage interview progression,
    time budgets, and stage-specific behavior directives.
    """
    def __init__(self, config: Optional[InterviewConfig] = None, initial_stage: InterviewStage = InterviewStage.GREETING):
        self.config = config or InterviewConfig()
        self.current_stage = initial_stage
        self.stage_turn_counts: Dict[str, int] = {s.value: 0 for s in STAGE_SEQUENCE}
        self.total_turns: int = 0
        self.start_time: float = time.perf_counter()
        self.stage_start_time: float = time.perf_counter()

    def get_budgets(self) -> List[StageBudget]:
        total_min = self.config.duration_minutes
        budgets = []
        for stage in STAGE_SEQUENCE:
            pct = STAGE_PERCENTAGES[stage]
            min_t, max_t = STAGE_TURN_BUDGETS[stage]
            budgets.append(StageBudget(
                stage=stage,
                display_name=STAGE_DISPLAY_NAMES[stage],
                target_duration_minutes=round(total_min * pct, 1),
                min_turns=min_t,
                max_turns=max_t
            ))
        return budgets

    def get_stage_directive(self, stage: Optional[InterviewStage] = None) -> str:
        active = stage or self.current_stage
        topics_str = ", ".join(self.config.topics)

        directives = {
            InterviewStage.GREETING: (
                "STAGE DIRECTIVE: [1. INTRODUCTION & GREETING]\n"
                "- Greet the candidate warmly, introduce yourself as VoiceHire.\n"
                "- Briefly outline the interview format and target duration.\n"
                "- Invite the candidate to introduce themselves and give a 1-minute high-level background."
            ),
            InterviewStage.RESUME_DEEP_DIVE: (
                "STAGE DIRECTIVE: [2. PAST PROJECTS & EXPERIENCE]\n"
                "- Probe the candidate on a significant technical project they architected or delivered.\n"
                "- Ask about their specific individual technical contributions, challenging bottlenecks, and tech stack choices.\n"
                "- Challenge them gently on why they picked specific databases or frameworks."
            ),
            InterviewStage.CORE_CONCEPTS: (
                f"STAGE DIRECTIVE: [3. CORE TECHNICAL CONCEPTS]\n"
                f"- Deeply evaluate the candidate's understanding of focus topics: {topics_str}.\n"
                "- Ask exact, probing conceptual questions (e.g. concurrency primitives, database indexing/isolation levels, caching strategies).\n"
                "- If the candidate answers well, increase depth; if they struggle, provide a brief hint and assess adaptability."
            ),
            InterviewStage.SYSTEM_DESIGN: (
                "STAGE DIRECTIVE: [4. SYSTEM ARCHITECTURE & DESIGN]\n"
                "- Present a realistic scalable system design scenario matching their role.\n"
                "- Ask them to outline high-level architecture: API layer, caching, database sharding, and message queues.\n"
                "- Probe specific single points of failure (SPOF) and consistency vs availability trade-offs."
            ),
            InterviewStage.CANDIDATE_QUESTIONS: (
                "STAGE DIRECTIVE: [5. CANDIDATE Q&A]\n"
                "- Transition smoothly by saying: 'We have covered the core technical topics. Now I would love to answer any questions you have for me.'\n"
                "- Answer their questions about the engineering culture, stack, or developer workflow constructively."
            ),
            InterviewStage.WRAP_UP: (
                "STAGE DIRECTIVE: [6. WRAP-UP & CLOSING]\n"
                "- Thank the candidate warmly for their time and technical insights today.\n"
                "- Inform them that the evaluation report has been recorded and the recruiting team will be in touch with next steps.\n"
                "- Deliver a brief, encouraging closing statement and conclude the session."
            )
        }
        return directives.get(active, "")

    def step_turn(self, last_candidate_reply: str = "", elapsed_seconds: float = 0.0) -> StageTransitionResult:
        """
        Record turn completion and evaluate if stage transition criteria are satisfied.
        """
        self.stage_turn_counts[self.current_stage.value] += 1
        self.total_turns += 1

        prev_stage = self.current_stage
        current_stage_turns = self.stage_turn_counts[self.current_stage.value]
        min_turns, max_turns = STAGE_TURN_BUDGETS[self.current_stage]

        current_stage_idx = STAGE_SEQUENCE.index(self.current_stage)
        total_stages = len(STAGE_SEQUENCE)

        # Check transition criteria (either exceeded max turns or reached min turns with natural stage conclusion)
        should_advance = False
        if current_stage_turns >= max_turns and current_stage_idx < total_stages - 1:
            should_advance = True
        elif current_stage_turns >= min_turns and current_stage_idx < total_stages - 1:
            # Transition on conversational cues
            reply_lower = last_candidate_reply.lower()
            if self.current_stage == InterviewStage.GREETING and len(last_candidate_reply.split()) > 10:
                should_advance = True
            elif self.current_stage == InterviewStage.CANDIDATE_QUESTIONS and ("no" in reply_lower or "that's all" in reply_lower or "thank" in reply_lower):
                should_advance = True

        if should_advance:
            self.current_stage = STAGE_SEQUENCE[current_stage_idx + 1]
            self.stage_start_time = time.perf_counter()
            logger.info("Advancing interview stage", extra={
                "previous_stage": prev_stage.value,
                "new_stage": self.current_stage.value,
                "total_turns": self.total_turns
            })

        new_stage_idx = STAGE_SEQUENCE.index(self.current_stage)
        progress_pct = round(((new_stage_idx + 1) / total_stages) * 100.0, 1)

        return StageTransitionResult(
            transitioned=should_advance,
            previous_stage=prev_stage,
            current_stage=self.current_stage,
            stage_display_name=STAGE_DISPLAY_NAMES[self.current_stage],
            progress_pct=progress_pct,
            stage_directive=self.get_stage_directive()
        )
