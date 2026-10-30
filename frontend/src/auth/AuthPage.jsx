import { useState } from "react";
import { Boxes, Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api, getErrorMessage } from "../services/api.js";
import { useAuth } from "./AuthContext.jsx";

const copy = {
  login: { title: "Welcome back", subtitle: "Sign in to your inventory workspace." },
  register: { title: "Create your account", subtitle: "Get started with your inventory workspace." },
  forgot: { title: "Reset your password", subtitle: "We’ll email you a secure password reset link." },
  reset: { title: "Choose a new password", subtitle: "Use at least 12 characters to keep your account secure." },
  verify: { title: "Verify your email", subtitle: "Confirm your email address to activate your account." },
};

function PasswordField({ id, label, value, onChange, autoComplete }) {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;
  return (
    <label className="auth-field" htmlFor={id}>
      <span>{label}</span>
      <span className="auth-input-wrap">
        <LockKeyhole size={17} aria-hidden="true" />
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          required
          minLength={id === "current-password" ? undefined : 12}
          maxLength={128}
        />
        <button
          className="password-visibility"
          type="button"
          aria-label={visible ? "Hide password" : "Show password"}
          onClick={() => setVisible((current) => !current)}
        >
          <Icon size={16} />
        </button>
      </span>
    </label>
  );
}

export default function AuthPage({ mode }) {
  const [values, setValues] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const content = copy[mode] || copy.login;

  const update = (key) => (event) => {
    setValues((current) => ({ ...current, [key]: event.target.value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (mode === "login") {
        await signIn({ email: values.email, password: values.password });
        const from = location.state?.from;
        const destination = from
          ? `${from.pathname}${from.search || ""}${from.hash || ""}`
          : "/";
        navigate(destination, { replace: true });
      } else if (mode === "register") {
        if (values.password !== values.confirm_password) throw new Error("Passwords do not match.");
        const { data } = await api.post("/auth/register", {
          full_name: values.full_name,
          email: values.email,
          password: values.password,
        });
        setMessage(data.message);
      } else if (mode === "forgot") {
        const { data } = await api.post("/auth/forgot-password", { email: values.email });
        setMessage(data.message);
      } else if (mode === "resend") {
        const { data } = await api.post("/auth/resend-verification", { email: values.email });
        setMessage(data.message);
      } else if (mode === "reset") {
        if (values.password !== values.confirm_password) throw new Error("Passwords do not match.");
        const { data } = await api.post("/auth/reset-password", {
          token: searchParams.get("token"),
          password: values.password,
        });
        setMessage(data.message);
      } else if (mode === "verify") {
        const { data } = await api.post("/auth/verify-email", {
          token: searchParams.get("token"),
        });
        setMessage(data.message);
      }
    } catch (requestError) {
      setError(requestError.response ? getErrorMessage(requestError) : requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const usesForm = mode !== "verify" || Boolean(searchParams.get("token"));
  const showEmail = ["login", "register", "forgot", "resend"].includes(mode);
  const showPassword = ["login", "register", "reset"].includes(mode);

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <Link className="auth-brand" to="/" aria-label="Inventory Desk">
          <span className="auth-brand-icon"><Boxes size={22} /></span>
          <span><strong>Inventory Desk</strong><small>STOCK CONTROL</small></span>
        </Link>
        <div className="auth-heading">
          <h1>{mode === "resend" ? "Resend verification" : content.title}</h1>
          <p>{mode === "resend" ? "Enter the email address you registered with." : content.subtitle}</p>
        </div>
        {error && <p className="auth-feedback auth-feedback-error" role="alert">{error}</p>}
        {message && <p className="auth-feedback auth-feedback-success" role="status">{message}</p>}
        {usesForm && !message && !(mode === "reset" && !searchParams.get("token")) && (
          <form className="auth-form" onSubmit={submit}>
            {mode === "register" && (
              <label className="auth-field" htmlFor="full-name">
                <span>Full name</span>
                <span className="auth-input-wrap">
                  <UserRound size={17} aria-hidden="true" />
                  <input id="full-name" autoComplete="name" value={values.full_name} onChange={update("full_name")} minLength={2} maxLength={100} required />
                </span>
              </label>
            )}
            {showEmail && (
              <label className="auth-field" htmlFor="email">
                <span>Email address</span>
                <span className="auth-input-wrap">
                  <Mail size={17} aria-hidden="true" />
                  <input id="email" type="email" autoComplete="email" value={values.email} onChange={update("email")} maxLength={254} required />
                </span>
              </label>
            )}
            {showPassword && (
              <PasswordField
                id="password"
                label={mode === "login" ? "Password" : "New password"}
                value={values.password}
                onChange={update("password")}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            )}
            {["register", "reset"].includes(mode) && (
              <PasswordField
                id="confirm-password"
                label="Confirm password"
                value={values.confirm_password}
                onChange={update("confirm_password")}
                autoComplete="new-password"
              />
            )}
            <button className="button button-primary auth-submit" disabled={busy}>
              {busy ? "Please wait..." : ({
                login: "Sign in",
                register: "Create account",
                forgot: "Send reset link",
                reset: "Update password",
                resend: "Send verification email",
                verify: "Verify email address",
              }[mode])}
            </button>
          </form>
        )}
        {mode === "verify" && !message && !error && !searchParams.get("token") && (
          <p className="auth-feedback auth-feedback-error" role="alert">
            This verification link is missing its token. Request another email below.
          </p>
        )}
        {mode === "reset" && !searchParams.get("token") && (
          <p className="auth-feedback auth-feedback-error" role="alert">
            This reset link is missing its token. Request a new password-reset email.
          </p>
        )}
        <nav className="auth-links" aria-label="Account options">
          {mode === "login" && <>
            <Link to="/forgot-password">Forgot password?</Link>
            <span>New here? <Link to="/register">Create an account</Link></span>
            <Link to="/resend-verification">Resend verification email</Link>
          </>}
          {mode === "register" && <span>Already have an account? <Link to="/login">Sign in</Link></span>}
          {["forgot", "reset", "verify", "resend"].includes(mode) && <Link to="/login">Back to sign in</Link>}
          {mode === "verify" && <Link to="/resend-verification">Resend verification email</Link>}
        </nav>
      </section>
      <p className="auth-privacy-note">Your password is securely hashed by the server and is never stored in your browser.</p>
    </main>
  );
}
