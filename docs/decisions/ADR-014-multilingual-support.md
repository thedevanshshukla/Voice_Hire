# ADR-014: Multilingual Support (English, Hindi & Hinglish) & Dynamic Code-Switching

## Status
Accepted (v0.14.0)

## Context
In modern software engineering interviews, especially across international engineering hubs (such as India), candidates frequently communicate in a hybrid mixture of English and Hindi ("Hinglish"). While core architectural terms, tool names, and metrics (*PostgreSQL, Kafka partition, TTL, Redis cache, Deadlock, Latency*) are universally expressed in English, conversational explanations and transitions often occur in Hindi. VoiceHire requires a multilingual engine capable of detecting pure English, Devanagari Hindi, and conversational Hinglish, dynamically code-switching and maintaining English technical vocabulary integrity.

## Decision
1. **Multilingual Architecture & Language Detection**:
   - `LanguageDetector`: Classifies incoming transcript turns into `ENGLISH`, `HINDI` (Devanagari Unicode), or `HINGLISH` (Romanized conversational vocabulary).
   - Detects code-switching mid-interview when a candidate transitions between English and Hindi/Hinglish.

2. **Technical Vocabulary Preservation & Hinglish Directives**:
   - `InterviewPromptBuilder` injects language-specific directives:
     - For **Hinglish**: Instructs the LLM to converse in natural professional Romanized Hindi while strictly retaining all technical terms (databases, algorithms, metrics) in English.
     - For **Hindi**: Devanagari script for speech synthesis while preserving English technical concepts.
     - For **English**: Standard professional English technical interviewing.

3. **STT & TTS Provider Configuration**:
   - Deepgram STT: Routes `en-US`, `en-IN`, `hi`, and `multi` models.
   - ElevenLabs TTS: Selects `eleven_multilingual_v2` for natural Hindi & Hinglish voice synthesis.

4. **REST APIs & WebSocket Notifications**:
   - `POST /api/voice/detect-language`: Language detection endpoint.
   - WebSockets emit `language_switched` event when code-switching is detected.
   - Live Language HUD Pill in the VoiceRoom header.

## Consequences
### Positive
- Delivers a natural interview experience for bilingual candidates without language friction.
- Avoids unnatural translations of standard English technical terminology.
- Supports dynamic language switching mid-session without restarting.

### Tradeoffs
- Requires STT models tuned for multilingual code-switching (`nova-2 multi`) for optimal transcript accuracy.
