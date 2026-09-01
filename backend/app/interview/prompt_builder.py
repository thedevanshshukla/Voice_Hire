from typing import Optional
from app.models.interview import InterviewConfig, InterviewRole, ExperienceLevel, InterviewLanguage, InterviewStage
from app.interview.state_machine import InterviewStateMachine
from app.interview.adaptive_engine import AdaptiveAction

class InterviewPromptBuilder:
    """
    Constructs dynamic, role-tailored, stage-conditioned, adaptively targeted,
    company RAG-grounded, cross-turn memory-aware, and multilingual (English, Hindi, Hinglish)
    system prompts for Voice AI interviews.
    """
    
    @staticmethod
    def build_system_prompt(
        config: InterviewConfig, 
        candidate_name: str = "Candidate",
        stage: Optional[InterviewStage] = None,
        adaptive_action: Optional[AdaptiveAction] = None,
        rag_context: Optional[str] = None,
        memory_context: Optional[str] = None,
        candidate_profile_context: Optional[str] = None,
        current_language: Optional[InterviewLanguage] = None
    ) -> str:
        topics_str = ", ".join(config.topics)
        active_lang = current_language or config.language

        if active_lang == InterviewLanguage.HINDI:
            lang_instruction = (
                "LANGUAGE DIRECTIVE: Conduct the entire interview strictly in Hindi using Devanagari script for speech synthesis. "
                "Keep core technical terms (e.g. PostgreSQL, Redis, Cache Stampede, Deadlock, Kafka) in their standard technical form."
            )
        elif active_lang == InterviewLanguage.HINGLISH:
            lang_instruction = (
                "LANGUAGE DIRECTIVE: Conduct the interview in natural, professional Hinglish (conversational Hindi flow with English technical terms). "
                "CRITICAL: Keep all technical terms, tool names, architectural concepts, and metrics strictly in English (e.g. 'PostgreSQL database', 'Cache invalidation', 'Redis cluster', 'Latency SLA'). "
                "Use conversational Romanized Hindi for framing questions (e.g. 'Aapne past project mein consistent hashing kaise implement kiya tha?')."
            )
        else:
            lang_instruction = "LANGUAGE DIRECTIVE: Conduct the entire interview strictly in professional English."

        jd_section = ""
        if config.job_description and len(config.job_description.strip()) > 10:
            jd_section = f"""
TARGET JOB DESCRIPTION & REQUIREMENTS:
\"\"\"
{config.job_description.strip()[:1000]}
\"\"\"
"""

        # Stage specific directive
        sm = InterviewStateMachine(config=config, initial_stage=stage or InterviewStage.GREETING)
        stage_directive = sm.get_stage_directive(stage=stage)

        # Adaptive engine directive
        adaptive_directive = ""
        if adaptive_action:
            adaptive_directive = f"\n{adaptive_action.guidance_directive}\n"

        # RAG Company Knowledge Base directive
        rag_directive = ""
        if rag_context and len(rag_context.strip()) > 0:
            rag_directive = f"""
[OFFICIAL COMPANY ENGINEERING STANDARD & RAG CONTEXT]:
\"\"\"
{rag_context.strip()}
\"\"\"
Use the above company standard to verify the technical precision of the candidate's answer and challenge them if their design contradicts these guidelines.
"""

        # Memory & Earlier Claims directive
        memory_directive = ""
        if memory_context and len(memory_context.strip()) > 0:
            memory_directive = f"\n{memory_context.strip()}\n"

        profile_directive = ""
        if candidate_profile_context and len(candidate_profile_context.strip()) > 0:
            profile_directive = f"""
[LONG-TERM CANDIDATE MULTI-ROUND PROFILE]:
\"\"\"
{candidate_profile_context.strip()}
\"\"\"
Avoid repeating previously asked questions from earlier rounds.
"""

        has_resume = bool(config.resume_text and len(config.resume_text.strip()) > 10)
        has_jd = bool(config.job_description and len(config.job_description.strip()) > 10)

        question_source_directive = ""
        if has_resume and has_jd:
            question_source_directive = f"""
[QUESTION GENERATION MANDATE - RESUME & JD CROSS-REFERENCING]:
1. You MUST formulate your technical questions by actively linking the candidate's Resume with the Job Description requirements (and vice-versa).
2. Specifically identify technologies, architectures, scale requirements, or challenges from the JD (e.g. distributed streaming, high-concurrency caching, microservices) and ask how the candidate applied or designed similar solutions in the projects listed on their resume.
3. Contrast their past resume experience against the JD requirements (e.g. "Our role requires handling high-write ingest with Kafka and Redis. I see on your resume you built a payments pipeline with PostgreSQL; how would you redesign that pipeline to meet our JD's latency SLA?").
4. Dig deeply into their specific resume contributions, metrics, tech stack choices, and architecture decisions while evaluating their suitability for the target role.
"""
        elif has_resume and not has_jd:
            question_source_directive = f"""
[QUESTION GENERATION MANDATE - 100% RESUME-GROUNDED QUESTIONS]:
1. No separate Job Description is provided. Therefore, ALL technical questions, deep dives, architecture probes, and system design questions MUST BE DRAWN DIRECTLY FROM THE CANDIDATE'S RESUME AND THE RELEVANT SURROUNDING ENGINEERING TOPICS.
2. Directly reference specific projects, companies, databases, tools, APIs, frameworks, and metrics written in their resume.
3. Challenge the candidate on the architectural mechanisms, trade-offs, bottlenecks, failure modes, and concurrency decisions of the systems they claim to have built.
4. Drill down on the technologies mentioned in their resume (e.g. if they list Redis, PostgreSQL, Docker, or Microservices, probe deeply into their internal mechanics and real-world implementations).
"""

        resume_section = ""
        if has_resume:
            resume_section = f"""
[CANDIDATE RESUME, WORK HISTORY & PROJECTS]:
\"\"\"
{config.resume_text.strip()[:4000]}
\"\"\"
CRITICAL RESUME INTERVIEWING INSTRUCTIONS:
- You have full access to the candidate's actual resume above.
- Act like an authentic, rigorous senior interviewer: Ask targeted questions about their specific past projects, companies, technologies, architectures, and achievements listed on their resume.
- Dig deep into claims made on their resume (e.g. asking how they implemented specific systems, why they chose certain databases, how they handled scale/failures in those projects).
- During the Project Deep Dive, Core Concepts, and System Design stages, probe directly into the projects and technologies they claim expertise in.
"""

        prompt = f"""You are VoiceHire, a senior staff technical interviewer conducting a live voice technical interview for a {config.role.value} position at the {config.experience_level.value} level.
Candidate Name: {candidate_name}
Target Duration: {config.duration_minutes} minutes
Selected Evaluation Topics: {topics_str}

{stage_directive}

{adaptive_directive}

{rag_directive}

{memory_directive}

{profile_directive}

{lang_instruction}

{question_source_directive}

{resume_section}

{jd_section}
INTERVIEWER BEHAVIOR GUIDELINES:
"""
        return prompt.strip()
