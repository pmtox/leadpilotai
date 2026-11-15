import React, { useEffect, useRef, useState } from 'react';
import { useVoice } from '../hooks/useVoice';
import {
  endConversation,
  sendAudioMessage,
  sendMessage,
  startConversation,
} from '../services/api';

const LANGUAGES = ['English', 'Hindi', 'Telugu', 'Tamil'];

function LeadSummary({ lead }) {
  if (!lead) {
    return <p className="muted-copy">Lead details appear here as the conversation progresses.</p>;
  }

  return (
    <div className="lead-summary">
      <div className="lead-summary-top">
        <div>
          <p className="eyebrow">LEAD QUALIFICATION</p>
          <strong className={`lead-status lead-${(lead.classification || 'cold').toLowerCase()}`}>
            {lead.classification || 'NEW'} LEAD
          </strong>
        </div>
        <div className="lead-score">{lead.score || 0}<span>/100</span></div>
      </div>
      <div className="score-track">
        <span style={{ width: `${Math.min(100, Math.max(0, lead.score || 0))}%` }} />
      </div>
      {lead.qualification_reason && (
        <p className="qualification-copy">{lead.qualification_reason}</p>
      )}
      <dl className="lead-facts">
        <div><dt>Business</dt><dd>{lead.business_type || 'Not shared yet'}</dd></div>
        <div><dt>Products</dt><dd>{lead.product_count?.toLocaleString('en-IN') || 'Not shared yet'}</dd></div>
        <div>
          <dt>Budget</dt>
          <dd>{lead.budget ? `₹${lead.budget.toLocaleString('en-IN')}` : 'Not shared yet'}</dd>
        </div>
        <div><dt>Launch</dt><dd>{lead.timeline || 'Not shared yet'}</dd></div>
        <div><dt>Intent</dt><dd>{lead.buying_intent || 'Not identified'}</dd></div>
      </dl>
      <div>
        <p className="eyebrow">FEATURES</p>
        {lead.features?.length ? (
          <div className="feature-list">
            {lead.features.map((feature) => <span className="feature-chip" key={feature}>{feature}</span>)}
          </div>
        ) : <p className="muted-copy">No features identified yet.</p>}
      </div>
    </div>
  );
}

export default function AIWorkspace({ profile, adminMode }) {
  const [language, setLanguage] = useState(profile.preferred_language || 'English');
  const [conversation, setConversation] = useState(null);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  async function handleAudioComplete(audio, filename, audioLanguage) {
    if (!conversation || conversation.status !== 'active') return;
    setLoading(true);
    setError('');
    try {
      const updated = await sendAudioMessage(conversation.id, audio, filename, audioLanguage);
      setConversation(updated);
      const latestMessage = updated.messages?.at(-1);
      if (latestMessage?.speaker === 'agent' && voiceEnabled) {
        speak(latestMessage.content, audioLanguage);
      }
    } catch (requestError) {
      setError(requestError.message || 'Could not send your voice message.');
    } finally {
      setLoading(false);
    }
  }

  const {
    isListening,
    startListening,
    stopListening,
    speak,
    voiceEnabled,
    toggleVoice,
    isSpeaking,
    voiceError,
    isSupported,
  } = useVoice({ language, onAudioComplete: handleAudioComplete });

  async function handleStartConversation() {
    setLoading(true);
    setError('');
    try {
      const started = await startConversation(profile.customer_id, language);
      setConversation(started);
      const greeting = started.messages?.find((message) => message.speaker === 'agent');
      if (greeting && voiceEnabled) speak(greeting.content, language);
    } catch (requestError) {
      setError(requestError.message || 'Could not start the AI conversation.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSendMessage(event) {
    event.preventDefault();
    if (!inputText.trim() || !conversation || loading) return;
    const message = inputText.trim();
    setInputText('');
    setLoading(true);
    setError('');
    try {
      const updated = await sendMessage(conversation.id, message, language);
      setConversation(updated);
      const latestMessage = updated.messages?.at(-1);
      if (latestMessage?.speaker === 'agent' && voiceEnabled) {
        speak(latestMessage.content, language);
      }
    } catch (requestError) {
      setInputText(message);
      setError(requestError.message || 'Could not send your message.');
    } finally {
      setLoading(false);
    }
  }

  async function handleEndConversation() {
    if (!conversation || loading) return;
    setLoading(true);
    setError('');
    try {
      const ended = await endConversation(conversation.id);
      setConversation(ended);
      window.speechSynthesis?.cancel();
    } catch (requestError) {
      setError(requestError.message || 'Could not end the conversation.');
    } finally {
      setLoading(false);
    }
  }

  function startNewConversation() {
    setConversation(null);
    setError('');
    window.speechSynthesis?.cancel();
  }

  const lead = conversation?.lead;

  return (
    <section className="page-section ai-page">
      <div className="page-heading ai-heading">
        <div>
          <p className="eyebrow">YOUR AI ASSISTANT</p>
          <h1>Let’s build your online store.</h1>
          <p>Talk through your idea, ask questions, and get a clear project summary.</p>
        </div>
        <button
          className={`voice-toggle ${voiceEnabled ? 'voice-toggle-on' : ''}`}
          type="button"
          onClick={toggleVoice}
          aria-pressed={voiceEnabled}
        >
          <span aria-hidden="true">{voiceEnabled ? '◖' : '◗'}</span>
          Voice {voiceEnabled ? 'on' : 'off'}
        </button>
      </div>

      <div className={`assistant-layout ${adminMode && conversation ? 'assistant-layout-admin' : ''}`}>
        <div className="assistant-main">
          {!conversation ? (
            <div className="surface assistant-welcome">
              <div className="assistant-orbit" aria-hidden="true"><span>✦</span></div>
              <p className="eyebrow">A THOUGHTFUL START</p>
              <h2>Tell me what you’re hoping to create.</h2>
              <p className="muted-copy">
                I’ll help you shape the idea into a practical plan, one question at a time.
              </p>
              <div className="language-picker" role="group" aria-label="Conversation language">
                {LANGUAGES.map((item) => (
                  <button
                    className={language === item ? 'language-option language-option-active' : 'language-option'}
                    key={item}
                    type="button"
                    onClick={() => setLanguage(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <p className="email-destination">
                Project summaries will use your account email: <strong>{profile.email}</strong>
              </p>
              <button
                className="button button-primary button-start"
                type="button"
                onClick={handleStartConversation}
                disabled={loading}
              >
                {loading ? 'Starting…' : 'Start a conversation'}
                <span aria-hidden="true">→</span>
              </button>
            </div>
          ) : (
            <div className="surface chat-panel">
              <header className="chat-header">
                <div className="chat-assistant-avatar" aria-hidden="true">✦</div>
                <div className="chat-title">
                  <strong>LeadPilot AI</strong>
                  <span>{isSpeaking ? 'Speaking now' : `${language} · Project assistant`}</span>
                </div>
                <span className={`conversation-state ${conversation.status === 'active' ? 'state-active' : ''}`}>
                  {conversation.status === 'active' ? 'In progress' : 'Completed'}
                </span>
                {conversation.status === 'active' ? (
                  <button className="button button-quiet" type="button" onClick={handleEndConversation} disabled={loading}>
                    End call
                  </button>
                ) : (
                  <button className="button button-quiet" type="button" onClick={startNewConversation}>
                    New conversation
                  </button>
                )}
              </header>

              <div className="chat-messages" aria-live="polite">
                {conversation.messages?.map((message) => {
                  const isAgent = message.speaker === 'agent';
                  return (
                    <div className={`message-row ${isAgent ? 'message-agent' : 'message-customer'}`} key={message.id}>
                      {isAgent && <div className="message-avatar" aria-hidden="true">✦</div>}
                      <div className="message-bubble">
                        <div className="message-meta">
                          <span>{isAgent ? 'LeadPilot AI' : 'You'}</span>
                          {isAgent && voiceEnabled && (
                            <button
                              className="message-speak"
                              type="button"
                              onClick={() => speak(message.content, language)}
                              aria-label="Read this reply aloud"
                            >
                              ◖
                            </button>
                          )}
                        </div>
                        <p>{message.content}</p>
                      </div>
                    </div>
                  );
                })}
                {loading && (
                  <div className="message-row message-agent">
                    <div className="message-avatar" aria-hidden="true">✦</div>
                    <div className="message-bubble message-thinking">Thinking<span>…</span></div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {conversation.status === 'active' && (
                <form className="chat-composer" onSubmit={handleSendMessage}>
                  <button
                    className={`mic-button ${isListening ? 'mic-button-live' : ''}`}
                    type="button"
                    onClick={isListening ? stopListening : startListening}
                    disabled={loading || !isSupported}
                    aria-label={isListening ? 'Stop recording' : 'Record a voice message'}
                    title={!isSupported ? 'Microphone needs a supported browser and HTTPS or localhost.' : undefined}
                  >
                    {isListening ? '■' : '◉'}
                  </button>
                  <input
                    className="chat-input"
                    value={inputText}
                    onChange={(event) => setInputText(event.target.value)}
                    disabled={loading}
                    placeholder={isListening ? 'Listening…' : 'Write a message or record your voice'}
                    aria-label="Your message"
                  />
                  <button className="button button-primary send-button" type="submit" disabled={loading || !inputText.trim()}>
                    Send
                  </button>
                </form>
              )}
              {(error || voiceError) && <p className="form-error chat-error" role="alert">{error || voiceError}</p>}
              {conversation.status === 'completed' && (
                <p className="email-destination completion-note">
                  Your project summary will be sent to <strong>{profile.email}</strong> if email delivery is configured.
                </p>
              )}
            </div>
          )}
          {error && !conversation && <p className="form-error" role="alert">{error}</p>}
        </div>

        {adminMode && conversation && (
          <aside className="surface admin-insights">
            <p className="eyebrow">ADMIN VIEW</p>
            <h2>Lead qualification</h2>
            <LeadSummary lead={lead} />
          </aside>
        )}
      </div>
    </section>
  );
}
