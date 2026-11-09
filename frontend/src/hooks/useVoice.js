import { useCallback, useEffect, useRef, useState } from 'react';

const LANGUAGE_CODES = {
  English: 'en-IN',
  Hindi: 'hi-IN',
  Telugu: 'te-IN'
};

function getRecordingError(error) {
  if (error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError') {
    return 'Microphone access was denied. Allow microphone access in your browser and try again.';
  }
  if (error?.name === 'NotFoundError' || error?.name === 'DevicesNotFoundError') {
    return 'No microphone was found. Connect a microphone and try again.';
  }
  if (error?.name === 'SecurityError') {
    return 'Microphone access requires localhost or a secure HTTPS connection.';
  }
  return error?.message || 'Could not start microphone recording.';
}

export function useVoice({ language = 'English', onAudioComplete }) {
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const onAudioCompleteRef = useRef(onAudioComplete);
  const listeningRef = useRef(false);

  useEffect(() => {
    onAudioCompleteRef.current = onAudioComplete;
  }, [onAudioComplete]);

  const isSupported = typeof window !== 'undefined'
    && Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);

  const releaseMicrophone = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recorderRef.current = null;
    listeningRef.current = false;
    setIsListening(false);
  }, []);

  const startListening = useCallback(async () => {
    if (listeningRef.current) return;
    setVoiceError('');

    if (!isSupported) {
      setVoiceError('Audio recording is unavailable. Use a current browser on localhost or HTTPS.');
      return;
    }

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
        .find((type) => window.MediaRecorder.isTypeSupported(type));
      const recorder = new window.MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onerror = (event) => {
        setVoiceError(getRecordingError(event.error));
        releaseMicrophone();
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm'
        });
        const extension = audioBlob.type.includes('mp4') ? 'm4a' : 'webm';
        releaseMicrophone();

        if (!audioBlob.size) {
          setVoiceError('No audio was recorded. Try speaking for a little longer.');
          return;
        }

        try {
          await onAudioCompleteRef.current?.(audioBlob, `recording.${extension}`, language);
        } catch (error) {
          setVoiceError(error.message || 'Audio transcription failed. Please try again.');
        }
      };

      recorderRef.current = recorder;
      listeningRef.current = true;
      recorder.start();
      setIsListening(true);
    } catch (error) {
      releaseMicrophone();
      setVoiceError(getRecordingError(error));
    }
  }, [isSupported, language, releaseMicrophone]);

  const stopListening = useCallback(() => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop();
    }
  }, []);

  const speak = useCallback((text, lang = language) => {
    if (!voiceEnabled || !window.speechSynthesis || !text) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const targetCode = LANGUAGE_CODES[lang] || 'en-IN';
    utterance.lang = targetCode;
    utterance.rate = 1;
    utterance.pitch = 1;

    const matchingVoice = window.speechSynthesis.getVoices()
      .find((voice) => voice.lang.startsWith(targetCode.slice(0, 2)));
    if (matchingVoice) utterance.voice = matchingVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [voiceEnabled, language]);

  const toggleVoice = useCallback(() => {
    if (voiceEnabled && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
    setVoiceEnabled((enabled) => !enabled);
  }, [voiceEnabled]);

  useEffect(() => () => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }, []);

  return {
    isListening,
    interimTranscript: '',
    startListening,
    stopListening,
    speak,
    voiceEnabled,
    toggleVoice,
    isSpeaking,
    voiceError,
    isSupported
  };
}
