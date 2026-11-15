import React, { useState } from 'react';

const LANGUAGES = ['English', 'Hindi', 'Telugu', 'Tamil'];

export default function ProfileView({ profile, onSave }) {
  const [language, setLanguage] = useState(profile.preferred_language || 'English');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');
    try {
      await onSave({ preferred_language: language });
      setMessage('Your preference has been saved.');
    } catch (saveError) {
      setError(saveError.message || 'Could not save your preference.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <p className="eyebrow">YOUR ACCOUNT</p>
          <h1>Profile</h1>
          <p>Manage your account details and AI conversation preference.</p>
        </div>
      </div>

      <div className="profile-grid">
        <article className="surface profile-card">
          <div className="profile-identity">
            {profile.picture ? (
              <img className="avatar avatar-large" src={profile.picture} alt="" referrerPolicy="no-referrer" />
            ) : (
              <div className="avatar avatar-large avatar-fallback" aria-hidden="true">
                {profile.name?.slice(0, 1)?.toUpperCase() || 'U'}
              </div>
            )}
            <div>
              <h2>{profile.name}</h2>
              <p>{profile.email}</p>
            </div>
          </div>
          <div className="profile-role">
            <span className="eyebrow">ACCOUNT TYPE</span>
            <span className={profile.role === 'admin' ? 'role-badge role-admin' : 'role-badge'}>
              {profile.role === 'admin' ? 'Administrator' : 'Member'}
            </span>
          </div>
          <p className="muted-copy">
            Your Google email is the destination for project summaries. You can update it in your Google account.
          </p>
        </article>

        <form className="surface profile-card" onSubmit={handleSubmit}>
          <p className="eyebrow">PREFERENCES</p>
          <h2>AI conversation language</h2>
          <p className="muted-copy">Choose the language your assistant should use by default.</p>
          <label className="field-label" htmlFor="preferred-language">Preferred language</label>
          <select
            id="preferred-language"
            className="text-field"
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
          >
            {LANGUAGES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          {message && <p className="form-success" role="status">{message}</p>}
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary" type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save preference'}
          </button>
        </form>
      </div>
    </section>
  );
}
