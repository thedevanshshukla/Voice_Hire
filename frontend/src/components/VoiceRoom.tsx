import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { InterviewSession } from './InterviewSetup';

interface VoiceMetrics {
  ttft_ms?: number;
  ttfa_ms?: number;
  llm_ttft_ms?: number;
  tts_ttfa_ms?: number;
  stt_latency_ms?: number;
  total_perceived_ms?: number;
  pause_count?: number;
  interrupted?: boolean;
  cancellation_latency_ms?: number;
  total_latency_ms?: number;
}

interface SessionScorecard {
  overall_score: number;
  avg_correctness: number;
  avg_depth: number;
  avg_clarity: number;
  avg_tradeoffs: number;
  avg_practical: number;
  total_evaluated_turns: number;
  passed_recommendation: boolean;
  summary_verdict: string;
  top_strengths: string[];
  areas_for_improvement: string[];
}

interface EvidenceSnippet {
  quote: string;
  topic: string;
  stage: string;
  dimension: string;
  rationale: string;
}

interface RedFlagItem {
  category: string;
  quote: string;
  severity: string;
  explanation: string;
}

interface EvidenceEvaluationReport {
  overall_confidence: string;
  confidence_score: number;
  recommendation: string;
  recommendation_reasoning: string;
  key_strengths_with_evidence: EvidenceSnippet[];
  key_weaknesses_with_evidence: EvidenceSnippet[];
  red_flags: RedFlagItem[];
}

interface TranscriptMessage {
  id: string;
  role: 'candidate' | 'interviewer' | 'system';
  text: string;
  stage?: string;
  metrics?: VoiceMetrics;
  isStreaming?: boolean;
  wasInterrupted?: boolean;
  timestamp: string;
}

interface VoiceRoomProps {
  apiUrl: string;
  activeSession?: InterviewSession | null;
  onClose?: () => void;
}

const STAGES = [
  { id: 'greeting', label: '1. Introduction', icon: '1' },
  { id: 'resume_deep_dive', label: '2. Project Deep Dive', icon: '2' },
  { id: 'core_concepts', label: '3. Technical Concepts', icon: '3' },
  { id: 'system_design', label: '4. System Architecture', icon: '4' },
  { id: 'candidate_questions', label: '5. Candidate Q&A', icon: '5' },
  { id: 'wrap_up', label: '6. Conclusion', icon: '6' }
];

export const VoiceRoom: React.FC<VoiceRoomProps> = ({ apiUrl, activeSession: propSession, onClose: _onClose }) => {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeSession, setActiveSession] = useState<InterviewSession | null>(propSession || null);
  const [roomName, setRoomName] = useState(paramSessionId || propSession?.session_id || 'interview-session-01');
  const [candidateName, setCandidateName] = useState(propSession?.candidate_name || user?.full_name || 'Candidate');
  
  const [isConnected, setIsConnected] = useState(false);
  const [_isMicPermissionGranted, setIsMicPermissionGranted] = useState(false);
  const [micVolumeLevel, setMicVolumeLevel] = useState<number>(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Session elapsed & countdown timer
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [timerInterval, setTimerInterval] = useState<any>(null);

  // 5-second silence countdown when candidate does not speak
  const [silenceCountdown, setSilenceCountdown] = useState<number | null>(null);

  const [vadState, setVadState] = useState<'idle' | 'speaking' | 'paused' | 'endpoint'>('idle');
  const [currentStage, setCurrentStage] = useState<string>('greeting');
  const [stageProgressPct, setStageProgressPct] = useState<number>(16.6);
  const [detectedLanguage, setDetectedLanguage] = useState<string>('English');

  const [sessionScorecard, setSessionScorecard] = useState<SessionScorecard | null>(null);
  const [evidenceReport, setEvidenceReport] = useState<EvidenceEvaluationReport | null>(null);
  const [showScorecardModal, setShowScorecardModal] = useState<boolean>(false);

  const [liveCandidateSpokenText, setLiveCandidateSpokenText] = useState('');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [agentStatus, setAgentStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<any>(null);
  const spokenBufferRef = useRef<string>('');
  const agentStatusRef = useRef<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const silenceTimerRef = useRef<any>(null);
  const keepAliveIntervalRef = useRef<any>(null);

  // Keep agentStatusRef in sync with agentStatus state
  useEffect(() => {
    agentStatusRef.current = agentStatus;
  }, [agentStatus]);

  // Handle 5-second silence countdown ticking
  useEffect(() => {
    if (silenceCountdown === null) {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      return;
    }

    if (silenceCountdown > 0) {
      silenceTimerRef.current = setTimeout(() => {
        setSilenceCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : null));
      }, 1000);
    } else if (silenceCountdown === 0) {
      // Auto-skip turn when candidate remains silent
      setSilenceCountdown(null);
      if (agentStatusRef.current === 'listening') {
        submitSpokenTurn("[Candidate remained silent / No response provided]");
      }
    }

    return () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    };
  }, [silenceCountdown]);

  // Pre-load speech synthesis voices
  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  // Fetch session details if routed directly via URL
  useEffect(() => {
    const fetchSession = async () => {
      const targetId = paramSessionId || propSession?.session_id;
      if (targetId && !activeSession) {
        try {
          const res = await fetch(`${apiUrl}/api/interview/session/${targetId}`);
          if (res.ok) {
            const data = await res.json();
            setActiveSession(data);
            setCandidateName(data.candidate_name);
            setRoomName(data.session_id);
            setDetectedLanguage(data.config?.language || 'English');
          }
        } catch (e) {
          console.warn('Could not fetch session details:', e);
        }
      }
    };
    fetchSession();
  }, [apiUrl, paramSessionId, propSession]);

  // Session timer hook
  useEffect(() => {
    if (isConnected) {
      const interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
      setTimerInterval(interval);
      return () => clearInterval(interval);
    } else {
      if (timerInterval) clearInterval(timerInterval);
    }
  }, [isConnected]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, liveCandidateSpokenText]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMicrophoneStream();
      cancelActiveAudio();
      stopSpeechRecognition();
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (keepAliveIntervalRef.current) clearInterval(keepAliveIntervalRef.current);
    };
  }, []);

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const cancelActiveAudio = () => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (keepAliveIntervalRef.current) {
      clearInterval(keepAliveIntervalRef.current);
      keepAliveIntervalRef.current = null;
    }
  };

  const stopMicrophoneStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
  };

  // Start continuous browser Speech Recognition for candidate
  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API not supported in this browser; using energy VAD.');
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = detectedLanguage === 'Hindi' ? 'hi-IN' : detectedLanguage === 'Hinglish' ? 'hi-IN' : 'en-US';

      rec.onresult = (event: any) => {
        // ONLY capture candidate speech when in listening mode (ignores laptop speaker feedback)
        if (agentStatusRef.current !== 'listening') return;

        let interim = '';
        let finalChunk = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalChunk += trans + ' ';
          } else {
            interim += trans;
          }
        }

        if (finalChunk) {
          spokenBufferRef.current += (spokenBufferRef.current ? ' ' : '') + finalChunk.trim();
        }

        const fullSpoken = (spokenBufferRef.current + ' ' + interim).trim();
        if (fullSpoken.length > 0) {
          setLiveCandidateSpokenText(fullSpoken);
          setVadState('speaking');
          // Cancel silence countdown when candidate starts speaking
          setSilenceCountdown(null);
        }
      };

      rec.onerror = (e: any) => {
        if (e.error !== 'no-speech') {
          console.warn('SpeechRecognition error:', e.error);
        }
      };

      rec.onend = () => {
        // Auto restart if still in listening mode so continuous candidate answers are never dropped
        if (agentStatusRef.current === 'listening') {
          try {
            rec.start();
          } catch (_) {}
        }
      };

      rec.start();
      recognitionRef.current = rec;
    } catch (err) {
      console.warn('Failed to start SpeechRecognition:', err);
    }
  };

  // Convert audio blob to Base64
  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        const base64 = (result && result.includes(',')) ? result.split(',')[1] : '';
        resolve(base64);
      };
      reader.readAsDataURL(blob);
    });
  };

  // Explicitly open microphone and start listening for candidate answer
  const startListeningForCandidate = () => {
    setAgentStatus('listening');
    setVadState('idle');
    spokenBufferRef.current = '';
    setLiveCandidateSpokenText('');
    setSilenceCountdown(5);

    stopSpeechRecognition();
    startSpeechRecognition();

    // Start studio audio recording for high-precision Deepgram Nova-2 STT
    audioChunksRef.current = [];
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      try {
        mediaRecorderRef.current.start(250);
      } catch (_) {}
    }
  };

  const stopListeningForCandidate = () => {
    setSilenceCountdown(null);
    stopSpeechRecognition();
  };

  // Request real microphone permissions and initiate Web Audio energy analyser & MediaRecorder
  const setupMicrophoneCapture = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 48000
        }
      });

      mediaStreamRef.current = stream;
      setIsMicPermissionGranted(true);

      // Setup MediaRecorder for studio-grade noise-isolated audio transmission to Deepgram
      try {
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4';

        const recorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond: 128000 });
        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };
        mediaRecorderRef.current = recorder;
      } catch (recErr) {
        console.warn('MediaRecorder setup fallback:', recErr);
      }

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      let isCandidateSpeaking = false;
      let lastSpeechTime = Date.now();

      const monitorAudioLevel = () => {
        if (!mediaStreamRef.current) return;
        analyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setMicVolumeLevel(normalized);

        const SPEECH_THRESHOLD = 18;
        if (normalized > SPEECH_THRESHOLD && !isMuted) {
          lastSpeechTime = Date.now();

          // Crucial: Only process candidate voice when the AI is NOT speaking (avoids speaker acoustic echo loop)
          if (agentStatusRef.current === 'listening') {
            setSilenceCountdown(null);
            if (!isCandidateSpeaking) {
              isCandidateSpeaking = true;
              setVadState('speaking');
            }
          }
        } else if (isCandidateSpeaking && agentStatusRef.current === 'listening') {
          // Candidate paused or stopped speaking
          const silenceDuration = Date.now() - lastSpeechTime;
          if (silenceDuration > 3500) {
            isCandidateSpeaking = false;
            setVadState('endpoint');
            
            // Auto-complete turn when candidate stops speaking for >3.5 seconds
            const textToSubmit = spokenBufferRef.current.trim() || liveCandidateSpokenText.trim();
            if (textToSubmit.length > 2) {
              spokenBufferRef.current = '';
              setLiveCandidateSpokenText('');
              submitSpokenTurn(textToSubmit);
            }
          } else if (silenceDuration > 800) {
            setVadState('paused');
          }
        }

        requestAnimationFrame(monitorAudioLevel);
      };

      requestAnimationFrame(monitorAudioLevel);
      return true;
    } catch (err) {
      console.error('Microphone permission error:', err);
      setErrorMsg('Microphone access was denied or is unavailable. Please grant microphone permissions to proceed.');
      setIsMicPermissionGranted(false);
      return false;
    }
  };

  // Speak AI interviewer question aloud with sentence chunking & SpeechSynthesis keep-alive
  const speakQuestionAloud = (text: string, audioBase64?: string, isFinalWrapUp: boolean = false) => {
    cancelActiveAudio();
    stopListeningForCandidate();
    setAgentStatus('speaking');
    setVadState('idle');
    setSilenceCountdown(null);

    const onSpeechFinished = () => {
      if (isFinalWrapUp) {
        // Automatic wrap-up: wait 1.2s and redirect directly to comprehensive evaluation report
        setAgentStatus('idle');
        setTimeout(() => {
          handleDisconnect();
        }, 1200);
      } else {
        // Seamlessly transition to listening mode and trigger fresh speech recognition
        startListeningForCandidate();
      }
    };

    // If audioBase64 audio bytes are valid
    if (audioBase64 && audioBase64.length > 400) {
      try {
        const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
        activeAudioRef.current = audio;
        audio.onended = () => {
          onSpeechFinished();
        };
        audio.onerror = () => {
          fallbackSpeechSynthesis(text, onSpeechFinished);
        };
        audio.play().catch(() => {
          fallbackSpeechSynthesis(text, onSpeechFinished);
        });
        return;
      } catch (_) {
        fallbackSpeechSynthesis(text, onSpeechFinished);
        return;
      }
    }

    fallbackSpeechSynthesis(text, onSpeechFinished);
  };

  const fallbackSpeechSynthesis = (text: string, onDone: () => void) => {
    if (!('speechSynthesis' in window)) {
      onDone();
      return;
    }
    window.speechSynthesis.cancel();
    if (keepAliveIntervalRef.current) clearInterval(keepAliveIntervalRef.current);

    const cleanText = text.replace(/[*_#`]/g, '').trim();
    if (!cleanText) {
      onDone();
      return;
    }

    // Split text into natural sentence chunks so Chrome engine never cuts off or pauses mid-speech
    const sentences = cleanText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [cleanText];
    let currentIndex = 0;

    const voices = window.speechSynthesis.getVoices();
    const highQualityVoice = voices.find(
      (v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Jenny') || v.name.includes('Zira') || v.name.includes('Aria'))
    ) || voices.find((v) => v.lang.startsWith('en'));

    // Heartbeat to keep Chrome speech synthesis running smoothly for long answers
    keepAliveIntervalRef.current = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        clearInterval(keepAliveIntervalRef.current);
      }
    }, 3500);

    const speakNextSentence = () => {
      if (currentIndex >= sentences.length) {
        if (keepAliveIntervalRef.current) clearInterval(keepAliveIntervalRef.current);
        onDone();
        return;
      }

      const segment = sentences[currentIndex].trim();
      currentIndex++;

      if (!segment) {
        speakNextSentence();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(segment);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      if (highQualityVoice) utterance.voice = highQualityVoice;

      utterance.onend = () => {
        speakNextSentence();
      };
      utterance.onerror = () => {
        speakNextSentence();
      };

      window.speechSynthesis.speak(utterance);
    };

    speakNextSentence();
  };

  const handleInterrupt = () => {
    cancelActiveAudio();
    startListeningForCandidate();
  };

  const refreshScorecardAndEvidence = async () => {
    const sessId = activeSession ? activeSession.session_id : roomName;
    try {
      const [scoreRes, evRes] = await Promise.all([
        fetch(`${apiUrl}/api/interview/session/${sessId}/scorecard`),
        fetch(`${apiUrl}/api/interview/session/${sessId}/evidence-report`)
      ]);
      if (scoreRes.ok) {
        const sc = await scoreRes.json();
        setSessionScorecard(sc);
      }
      if (evRes.ok) {
        const ev = await evRes.json();
        setEvidenceReport(ev);
      }
    } catch (e) {
      console.warn('Could not fetch updated scorecard/evidence:', e);
    }
  };

  // Submit candidate spoken turn to backend
  const submitSpokenTurn = async (spokenText: string) => {
    if (isProcessing || !spokenText.trim()) return;

    setIsProcessing(true);
    stopListeningForCandidate();
    setAgentStatus('thinking');
    setVadState('endpoint');

    const isSilentTurn = spokenText.includes('[Candidate remained silent');

    // Extract recorded candidate audio bytes
    let audioBase64: string | undefined = undefined;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          audioBase64 = await blobToBase64(audioBlob);
        }
      } catch (recErr) {
        console.warn('Audio export fallback:', recErr);
      }
    }

    const candidateMsgId = `user-${Date.now()}`;
    const userMsg: TranscriptMessage = {
      id: candidateMsgId,
      role: 'candidate',
      stage: currentStage,
      text: isSilentTurn ? '(No response / Candidate remained silent)' : spokenText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);

    try {
      const historyPayload = [...messages, userMsg].map((m) => ({
        role: m.role === 'interviewer' ? 'assistant' : 'user',
        content: m.text
      }));

      const response = await fetch(`${apiUrl}/api/voice/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession ? activeSession.session_id : roomName,
          text: spokenText,
          audio_base64: audioBase64,
          history: historyPayload
        })
      });

      if (!response.ok) {
        throw new Error(`Turn endpoint error: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.detected_language) setDetectedLanguage(data.detected_language);
      if (data.current_stage) setCurrentStage(data.current_stage);
      if (data.progress_pct) setStageProgressPct(data.progress_pct);

      // Update candidate message with Deepgram's high-precision transcript if available
      if (data.transcript && data.transcript.trim() && !isSilentTurn) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === candidateMsgId ? { ...msg, text: data.transcript } : msg
          )
        );
      }

      const agentMsg: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
        stage: data.current_stage || currentStage,
        text: data.response_text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };

      setMessages((prev) => [...prev, agentMsg]);

      // Check if this response is the concluding wrap-up / farewell statement
      const lowerReply = (data.response_text || '').toLowerCase();
      const isWrapUp = data.current_stage === 'wrap_up' || 
                       lowerReply.includes('future opportunities') ||
                       lowerReply.includes('best of luck') ||
                       lowerReply.includes('concludes our interview') ||
                       lowerReply.includes('thank you for your time') ||
                       lowerReply.includes('have a great day');

      speakQuestionAloud(data.response_text, data.audio_base64, isWrapUp);
    } catch (err: any) {
      console.error('Turn error:', err);
      setErrorMsg(err.message || 'Error processing speech turn');
      startListeningForCandidate();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualSubmitEarly = () => {
    const textToSubmit = spokenBufferRef.current.trim() || liveCandidateSpokenText.trim();
    if (textToSubmit.length > 0) {
      spokenBufferRef.current = '';
      setLiveCandidateSpokenText('');
      submitSpokenTurn(textToSubmit);
    }
  };

  const handleConnect = async () => {
    setErrorMsg(null);
    const micOk = await setupMicrophoneCapture();
    if (!micOk) return;

    try {
      const sessId = activeSession ? activeSession.session_id : roomName;
      const response = await fetch(`${apiUrl}/api/voice/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: sessId,
          identity: `candidate-${Date.now().toString().slice(-4)}`,
          name: candidateName,
          session_id: sessId
        })
      });

      if (!response.ok) {
        throw new Error(`Token generation failed: ${response.statusText}`);
      }

      await response.json();
      setIsConnected(true);
      setAgentStatus('thinking');

      // Request opening greeting turn from AI Interviewer
      const turnResp = await fetch(`${apiUrl}/api/voice/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessId,
          text: '',
          history: []
        })
      });

      if (turnResp.ok) {
        const turnData = await turnResp.json();
        const initialGreetingText = turnData.response_text || `Hello ${candidateName}, welcome to your technical interview. I will be conducting your assessment today. To get started, please tell me about yourself and your recent engineering projects.`;
        const initialGreeting: TranscriptMessage = {
          id: `agent-${Date.now()}`,
          role: 'interviewer',
          stage: turnData.current_stage || 'greeting',
          text: initialGreetingText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        };
        setMessages([initialGreeting]);
        speakQuestionAloud(initialGreetingText, turnData.audio_base64);
      } else {
        const fallbackText = `Hello ${candidateName}, welcome to your technical assessment. I will be your interviewer today. To begin, please introduce yourself and tell me about a recent engineering project you worked on.`;
        const fallbackGreeting: TranscriptMessage = {
          id: `agent-${Date.now()}`,
          role: 'interviewer',
          stage: 'greeting',
          text: fallbackText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        };
        setMessages([fallbackGreeting]);
        speakQuestionAloud(fallbackText);
      }
    } catch (err: any) {
      console.error('Connection error:', err);
      setErrorMsg(err.message || 'Failed to connect to voice room');
      setIsConnected(false);
      setAgentStatus('idle');
    }
  };

  const handleDisconnect = () => {
    cancelActiveAudio();
    stopMicrophoneStream();
    stopListeningForCandidate();
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (keepAliveIntervalRef.current) clearInterval(keepAliveIntervalRef.current);
    setIsConnected(false);
    setAgentStatus('idle');
    setVadState('idle');

    // Route to final report view
    const sessId = activeSession ? activeSession.session_id : roomName;
    navigate(`/report/${sessId}`);
  };

  const getStageIndex = (stageId: string) => STAGES.findIndex((s) => s.id === stageId);
  const totalDurationSeconds = (activeSession?.config.duration_minutes || 30) * 60;
  const remainingSeconds = Math.max(0, totalDurationSeconds - elapsedSeconds);

  return (
    <div className="voice-room-container">
      {/* Header bar */}
      <div className="voice-room-header">
        <div className="room-info">
          <button className="btn-back-link" onClick={() => navigate('/dashboard')} style={{ marginRight: '12px' }}>
            ← Back to Dashboard
          </button>
          <div className={`status-indicator ${isConnected ? 'active' : 'inactive'}`} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 className="room-title">
                {activeSession ? `${activeSession.config.role} Interview` : `Interview Session`}
              </h3>
              {activeSession && (
                <span className="badge badge-sm">{activeSession.config.experience_level}</span>
              )}
            </div>
            <span className="room-subtitle">
              {isConnected ? `Candidate: ${candidateName}` : 'Ready to begin assessment'}
            </span>
          </div>
        </div>

        {/* Live Session Timer (Prominent & Centered) */}
        {isConnected && (
          <div className="session-timer-badge">
            <span className="timer-icon">⏱️</span>
            <span>Elapsed: {formatTimer(elapsedSeconds)}</span>
            <span className="timer-divider">•</span>
            <span style={{ color: remainingSeconds < 300 ? '#f87171' : '#a78bfa' }}>
              {formatTimer(remainingSeconds)} Left
            </span>
          </div>
        )}

        <div className="room-actions">
          {isConnected && (
            <>
              <button 
                className="btn btn-secondary btn-scorecard-btn"
                onClick={() => {
                  refreshScorecardAndEvidence();
                  setShowScorecardModal(true);
                }}
              >
                <span>Recruiter Scorecard</span>
              </button>
              <button className="btn btn-end-interview-top" onClick={handleDisconnect}>
                <span>⏹️ End Interview & View Report</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* 6-Stage Progression Timeline */}
      {isConnected && (
        <div className="stage-timeline-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '900px', margin: '0 auto 8px auto' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
              Assessment Progression
            </span>
            <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: 700, color: 'var(--accent-purple)' }}>
              {stageProgressPct}% Complete
            </span>
          </div>
          <div className="stage-timeline">
            {STAGES.map((s, idx) => {
              const currentIndex = getStageIndex(currentStage);
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;
              return (
                <div 
                  key={s.id} 
                  className={`timeline-step ${isPast ? 'completed' : ''} ${isCurrent ? 'active' : ''}`}
                >
                  <div className="step-bullet">
                    {isPast ? '✓' : s.icon}
                  </div>
                  <span className="step-label">{s.label}</span>
                  {idx < STAGES.length - 1 && <div className="step-connector"></div>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="error-banner">
          {errorMsg}
        </div>
      )}

      {/* Recruiter Evaluation Modal */}
      {showScorecardModal && (
        <div className="scorecard-modal-backdrop" onClick={() => setShowScorecardModal(false)}>
          <div className="scorecard-modal" onClick={(e) => e.stopPropagation()}>
            <div className="scorecard-modal-header">
              <div>
                <h3 style={{ margin: 0 }}>Recruiter Assessment Audit</h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {candidateName} • {activeSession?.config.role}
                </span>
              </div>
              <button className="btn-close" onClick={() => setShowScorecardModal(false)}>✕</button>
            </div>

            <div className="scorecard-modal-body">
              <div className="scorecard-hero">
                <div className="hero-score-val">
                  {sessionScorecard?.overall_score.toFixed(1) || '0.0'}
                  <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 5.0</span>
                </div>
                <div className="hero-verdict">
                  <div className="verdict-label">Recommendation</div>
                  <div className="verdict-title">{evidenceReport?.recommendation || sessionScorecard?.summary_verdict || 'Evaluating'}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {sessionScorecard?.total_evaluated_turns || 0} answers analyzed
                  </div>
                </div>
              </div>

              <div className="dimensions-breakdown">
                <h4>Competency Breakdown</h4>
                <div className="dim-row">
                  <div className="dim-header">
                    <span>1. Correctness</span>
                    <span className="dim-val">{sessionScorecard?.avg_correctness.toFixed(1) || '0.0'} / 5.0</span>
                  </div>
                  <div className="dim-bar-bg"><div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_correctness || 0) / 5) * 100}%` }}></div></div>
                </div>
                <div className="dim-row">
                  <div className="dim-header">
                    <span>2. Depth & Mechanics</span>
                    <span className="dim-val">{sessionScorecard?.avg_depth.toFixed(1) || '0.0'} / 5.0</span>
                  </div>
                  <div className="dim-bar-bg"><div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_depth || 0) / 5) * 100}%`, background: 'var(--accent-purple)' }}></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Room Body */}
      {!isConnected ? (
        <div className="connection-setup-card">
          <h2>Ready to Begin Technical Assessment</h2>
          <p className="setup-description">
            The interview is conducted entirely over voice. Please ensure you are in a quiet environment and allow microphone access when prompted.
          </p>

          <div className="mic-check-preview-box">
            <div className="mic-check-icon">🎙</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px' }}>Microphone Permission Required</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Your audio will be analyzed in real time for architectural and technical depth.
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>Candidate Name</label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="input-field"
              placeholder="e.g. Alex Chen"
            />
          </div>

          <button className="btn btn-primary btn-full btn-lg" onClick={handleConnect}>
            <span>Allow Microphone & Start Interview</span>
            <span>→</span>
          </button>
        </div>
      ) : (
        <div className="active-room-layout">
          {/* Visualizer & Mic Level HUD */}
          <div className="agent-visualizer-card">
            <div className="status-row">
              {/* Recording Indicator */}
              <div className="recording-live-pill">
                <span className="recording-dot"></span>
                <span>Recording Active</span>
              </div>

              {/* Turn State Badge */}
              <div className={`turn-state-badge ${agentStatus}`}>
                {agentStatus === 'speaking' && '🎙️ AI Interviewer Speaking...'}
                {agentStatus === 'listening' && (vadState === 'speaking' ? '🗣️ Candidate Speaking...' : '🟢 Listening (Your Turn to Speak)')}
                {agentStatus === 'thinking' && '⏳ Formulating Next Question...'}
                {agentStatus === 'idle' && 'Connected'}
              </div>

              {/* Silence / No-Response Countdown Warning Pill */}
              {agentStatus === 'listening' && silenceCountdown !== null && (
                <div className="silence-countdown-pill">
                  ⏱️ Auto-skipping in {silenceCountdown}s
                </div>
              )}

              {/* Language Pill */}
              <div className="language-hud-pill">
                {detectedLanguage}
              </div>

              {/* Interruption Trigger */}
              {agentStatus === 'speaking' && (
                <button className="btn-barge-in" onClick={handleInterrupt}>
                  Interrupt Agent
                </button>
              )}
            </div>

            {/* Live Audio Waveform & Mic Level Meter */}
            <div className={`waveform-visualizer ${agentStatus}`}>
              <div className="bar bar-1"></div>
              <div className="bar bar-2"></div>
              <div className="bar bar-3"></div>
              <div className="bar bar-4"></div>
              <div className="bar bar-5"></div>
              <div className="bar bar-6"></div>
              <div className="bar bar-7"></div>
            </div>

            {/* Candidate Microphone Level Meter Bar */}
            <div className="mic-level-monitor">
              <span className="mic-icon-lbl">{isMuted ? '🔇' : '🎙️'}</span>
              <div className="mic-meter-bar-bg">
                <div className="mic-meter-bar-fill" style={{ width: `${isMuted ? 0 : micVolumeLevel}%` }}></div>
              </div>
            </div>

            <div className="agent-state-label">
              {agentStatus === 'listening' && (
                silenceCountdown !== null
                  ? `⏱️ Waiting for your answer... (${silenceCountdown}s remaining before moving forward)`
                  : '🟢 Your turn to speak. The interviewer is listening to your answer...'
              )}
              {agentStatus === 'thinking' && '⏳ Analyzing answer and formulating follow-up question...'}
              {agentStatus === 'speaking' && '🎙️ AI Interviewer speaking question (Listen)...'}
              {agentStatus === 'idle' && 'Connected'}
            </div>
          </div>

          {/* Conversation Transcript Stream */}
          <div className="chat-stream-card">
            <div className="chat-messages-scroll">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-bubble-wrapper ${msg.role}`}>
                  <div className={`chat-bubble ${msg.role} ${msg.isStreaming ? 'streaming' : ''} ${msg.wasInterrupted ? 'interrupted' : ''}`}>
                    <div className="bubble-header">
                      <span className="bubble-sender">
                        {msg.role === 'interviewer' ? 'AI Interviewer' : candidateName}
                      </span>
                      {msg.stage && (
                        <span className="bubble-stage-badge">
                          {msg.stage.replace('_', ' ').toUpperCase()}
                        </span>
                      )}
                      <span className="bubble-time">{msg.timestamp}</span>
                    </div>

                    <div className="bubble-content">
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))}

              {/* Live In-Progress Spoken Speech Bubble */}
              {agentStatus === 'listening' && liveCandidateSpokenText && (
                <div className="chat-bubble-wrapper candidate">
                  <div className="chat-bubble candidate live-preview">
                    <div className="bubble-header">
                      <span className="bubble-sender">{candidateName} (Speaking...)</span>
                      <span className="bubble-stage-badge">LIVE MIC</span>
                    </div>
                    <div className="bubble-content">
                      {liveCandidateSpokenText}
                      <span className="recording-dot" style={{ display: 'inline-block', marginLeft: '6px' }}></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={transcriptEndRef} />
            </div>

            {/* Voice-Only Bottom Action Controls */}
            <div className="voice-only-controls-bar" style={{ justifyContent: 'center', gap: '14px' }}>
              <button
                type="button"
                className={`btn btn-mic ${isMuted ? 'muted' : 'active'}`}
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? '🔇 Microphone Muted (Click to Unmute)' : '🎙️ Microphone Active'}
              </button>

              {agentStatus === 'listening' && (liveCandidateSpokenText.trim().length > 0 || vadState === 'speaking') && (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={handleManualSubmitEarly}
                  style={{ borderRadius: '20px', padding: '8px 18px', fontWeight: 600 }}
                >
                  ✓ Finish Answer Now
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
