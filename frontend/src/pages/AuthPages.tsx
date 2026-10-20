import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

function AuthFrame({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="brand auth-brand" to="/login">
          <span className="brand-mark" aria-hidden="true">d.</span>
          <span>daymark<span className="brand-period">.</span></span>
        </Link>
        <p className="eyebrow">A CLEARER KIND OF PRODUCTIVITY</p>
        <h1>{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>
        {children}
        <div className="auth-footer">{footer}</div>
      </section>
      <aside className="auth-aside">
        <div className="auth-aside-copy">
          <span className="auth-sparkle" aria-hidden="true">✳</span>
          <p>Make space for the work<br />that moves you forward.</p>
          <span className="auth-aside-caption">One thoughtful step at a time.</span>
        </div>
        <div className="auth-orbit orbit-one" />
        <div className="auth-orbit orbit-two" />
      </aside>
    </main>
  );
}

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/"} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const signedInUser = await signIn(email.trim(), password);
      const destination =
        (location.state as { from?: string } | null)?.from ??
        (signedInUser.role === "admin" ? "/admin" : "/");
      navigate(destination, { replace: true });
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Sign-in failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame
      title="Welcome back"
      subtitle="Sign in to pick up where you left off."
      footer={<>New to Daymark? <Link to="/register">Create an account</Link></>}
    >
      <form className="form-stack" onSubmit={submit}>
        {error && <p className="alert alert-error" role="alert">{error}</p>}
        <label className="field">
          <span>Email address</span>
          <input
            autoComplete="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            autoComplete="current-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Your password"
            required
          />
        </label>
        <button className="button button-primary button-full" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"} <span aria-hidden="true">→</span>
        </button>
      </form>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const { user, signUp } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/"} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setBusy(true);
    try {
      await signUp(fullName.trim(), email.trim(), password);
      setSuccess("Your account is ready. Sign in to continue.");
      window.setTimeout(() => navigate("/login", { replace: true }), 700);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Registration failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame
      title="Create your space"
      subtitle="A few details and you're ready to go."
      footer={<>Already have an account? <Link to="/login">Sign in</Link></>}
    >
      <form className="form-stack" onSubmit={submit}>
        {error && <p className="alert alert-error" role="alert">{error}</p>}
        {success && <p className="alert alert-success" role="status">{success}</p>}
        <label className="field">
          <span>Full name</span>
          <input
            autoComplete="name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            maxLength={200}
            placeholder="How should we address you?"
            required
          />
        </label>
        <label className="field">
          <span>Email address</span>
          <input
            autoComplete="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>
        <label className="field">
          <span>Password <small>At least 12 characters</small></span>
          <input
            autoComplete="new-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={12}
            maxLength={128}
            placeholder="Create a secure password"
            required
          />
        </label>
        <button className="button button-primary button-full" disabled={busy}>
          {busy ? "Creating account…" : "Create account"} <span aria-hidden="true">→</span>
        </button>
      </form>
    </AuthFrame>
  );
}
