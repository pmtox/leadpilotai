import React, { useEffect, useState } from 'react';
import { fetchAuthStatus, googleLoginUrl } from '../services/api';

const AUTH_ERROR_MESSAGES = {
  google_not_configured: 'Google sign-in is not configured yet. Ask your administrator to finish setup.',
  google_signin_failed: 'Google sign-in could not be completed. Please try again.',
  google_email_unverified: 'Use a Google account with a verified email address.',
};

export default function GoogleLoginView({ initialError = '' }) {
  const [googleConfigured, setGoogleConfigured] = useState(false);
  const [checking, setChecking] = useState(true);
  const queryError = AUTH_ERROR_MESSAGES[new URLSearchParams(window.location.search).get('auth_error')] || '';
  const [error, setError] = useState(queryError || initialError);

  useEffect(() => {
    fetchAuthStatus()
      .then((status) => setGoogleConfigured(status.google_configured))
      .catch(() => setError('Could not connect to LeadPilot. Check that the backend is running.'))
      .finally(() => setChecking(false));
  }, []);

  function signIn() {
    window.location.assign(googleLoginUrl());
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="brand-mark" aria-hidden="true">L</div>
        <p className="eyebrow">LEADPILOT AI</p>
        <h1>Your next great idea<br />starts with a conversation.</h1>
        <p className="login-copy">
          Plan your online store with a personal AI assistant. Sign in to continue.
        </p>

        {error && <div className="notice notice-error" role="alert">{error}</div>}
        {!checking && !googleConfigured && !error && (
          <div className="notice">
            Google sign-in needs to be configured by the administrator before you can continue.
          </div>
        )}

        <button
          className="button button-google"
          type="button"
          onClick={signIn}
          disabled={checking || !googleConfigured}
        >
          <span className="google-g" aria-hidden="true">G</span>
          {checking ? 'Checking sign-in…' : 'Continue with Google'}
        </button>
        <p className="login-footnote">
          Your Google email is used for your account and project-summary emails.
        </p>
      </section>
      <footer className="login-footer">Private, secure project planning with LeadPilot AI</footer>
    </main>
  );
}
