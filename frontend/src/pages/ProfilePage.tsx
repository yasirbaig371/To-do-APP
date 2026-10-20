import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { changeMyPassword, updateMyProfile } from "../api/users";
import { ErrorMessage, PageHeader } from "../components/Shared";

export function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [profileError, setProfileError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [profileNotice, setProfileNotice] = useState("");
  const [passwordNotice, setPasswordNotice] = useState("");
  const [profileBusy, setProfileBusy] = useState(false);
  const [passwordBusy, setPasswordBusy] = useState(false);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError("");
    setProfileNotice("");
    setProfileBusy(true);
    try {
      const updated = await updateMyProfile({
        full_name: name.trim(),
        email: email.trim(),
      });
      updateUser(updated);
      setProfileNotice("Your profile has been updated.");
    } catch (cause) {
      setProfileError(cause instanceof ApiError ? cause.message : "Could not update your profile.");
    } finally {
      setProfileBusy(false);
    }
  }

  async function savePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");
    setPasswordNotice("");
    if (newPassword !== confirmPassword) {
      setPasswordError("The new passwords do not match.");
      return;
    }
    setPasswordBusy(true);
    try {
      await changeMyPassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordNotice("Password changed. Your current session remains active.");
    } catch (cause) {
      setPasswordError(cause instanceof ApiError ? cause.message : "Could not change your password.");
    } finally {
      setPasswordBusy(false);
    }
  }

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="YOUR ACCOUNT"
        title="Profile & security"
        subtitle="Keep your details current and your account protected."
      />
      <div className="profile-grid">
        <section className="panel profile-panel">
          <div className="panel-heading">
            <div className="profile-avatar-large">{user?.full_name.slice(0, 1).toUpperCase()}</div>
            <div><p className="eyebrow">PERSONAL DETAILS</p><h2>Your profile</h2></div>
          </div>
          {profileError && <ErrorMessage message={profileError} />}
          {profileNotice && <p className="alert alert-success" role="status">{profileNotice}</p>}
          <form className="form-stack" onSubmit={saveProfile}>
            <label className="field">
              <span>Full name</span>
              <input value={name} onChange={(event) => setName(event.target.value)} maxLength={200} required />
            </label>
            <label className="field">
              <span>Email address</span>
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <label className="field">
              <span>Account role</span>
              <input value={user?.role === "admin" ? "Administrator" : "Member"} disabled />
            </label>
            <button className="button button-primary" disabled={profileBusy}>
              {profileBusy ? "Saving…" : "Save profile"}
            </button>
          </form>
        </section>
        <section className="panel profile-panel">
          <div className="panel-heading">
            <div className="panel-icon" aria-hidden="true">⌑</div>
            <div><p className="eyebrow">ACCOUNT SECURITY</p><h2>Change password</h2></div>
          </div>
          {passwordError && <ErrorMessage message={passwordError} />}
          {passwordNotice && <p className="alert alert-success" role="status">{passwordNotice}</p>}
          <form className="form-stack" onSubmit={savePassword}>
            <label className="field">
              <span>Current password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                maxLength={128}
                required
              />
            </label>
            <label className="field">
              <span>New password <small>At least 12 characters</small></span>
              <input
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={12}
                maxLength={128}
                required
              />
            </label>
            <label className="field">
              <span>Confirm new password</span>
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                minLength={12}
                maxLength={128}
                required
              />
            </label>
            <button className="button button-secondary" disabled={passwordBusy}>
              {passwordBusy ? "Updating…" : "Update password"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
