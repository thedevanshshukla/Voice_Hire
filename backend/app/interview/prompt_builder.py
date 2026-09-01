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

        resume_section = ""
        if config.resume_text and len(config.resume_text.strip()) > 10:
            resume_section = f"""
[CANDIDATE RESUME, WORK HISTORY & PROJECTS]:
\"\"\"
{config.resume_text.strip()[:3500]}
\"\"\"
CRITICAL RESUME INTERVIEWING INSTRUCTIONS:
- You have full access to the candidate's actual resume above.
- Act like an authentic, rigorous senior interviewer: Ask targeted questions about their specific past projects, companies, technologies, architectures, and achievements listed on their resume.
- Connect the candidate's resume experience directly with the Target Job Description requirements.
- Dig deep into claims made on their resume (e.g. asking how they implemented specific systems, why they chose certain databases, how they handled scale/failures in those projects).
- During the Project Deep Dive and Technical stages, probe both directly ("I see you worked on X at Y company...") and conceptually around the technologies they claim expertise in.
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

{resume_section}

{jd_section}
INTERVIEWER BEHAVIOR GUIDELINES:
1. CONVERSATIONAL & CONCISE: This is a realtime voice conversation. Keep all questions and explanations under 2 to 3 sentences so the candidate has room to speak. NEVER give long monologues.
2. ONE QUESTION AT A TIME: Ask exactly ONE clear technical question at a time. Do not overload the candidate with multi-part questions in a single turn.
3. ADAPTIVE DEPTH & RESUME PROBING: 
   - Ask specific, authentic questions grounded in their uploaded resume projects and link them to the target job description.
   - For SDE-1: Focus on core fundamentals, data structures, basic queries, and memory concepts.
   - For SDE-2 / Senior: Focus on concurrency, failure modes, trade-offs, scalability, and distributed state.
   - For Staff: Focus on system boundaries, consensus, operational resilience, and architectural decisions.
4. RIGOROUS & EVIDENCE-BASED: If the candidate gives a shallow or incorrect answer, challenge them constructively with a targeted follow-up. If their answer is complete, transition smoothly to the next concept.
5. CROSS-TURN CONTINUITY: Naturally reference previous systems, tools, and databases the candidate described earlier to test architectural consistency.
6. NATURAL TONE: Be professional, encouraging, yet intellectually rigorous.
"""
        return prompt.strip()
