
import { useState } from "react";
import {
  Boxes,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  UserRound,
} from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api, getErrorMessage } from "../services/api.js";
import { useAuth } from "./AuthContext.jsx";

function PasswordField({
  id,
  label,
  value,
  onChange,
  autoComplete,
}) {
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
  const [values, setValues] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const { signIn } = useAuth();

  const currentMode = mode === "register" ? "register" : "login";
  const isRegister = currentMode === "register";

  const update = (key) => (event) => {
    setValues((current) => ({
      ...current,
      [key]: event.target.value,
    }));
  };

  const submit = async (event) => {
    event.preventDefault();

    setBusy(true);
    setError("");
    setMessage("");

    try {
      if (isRegister) {
        if (values.password !== values.confirm_password) {
          throw new Error("Passwords do not match.");
        }

        const { data } = await api.post("/auth/register", {
          full_name: values.full_name.trim(),
          email: values.email.trim(),
          password: values.password,
        });

        setMessage(
          data.message || "Registration successful. Please sign in."
        );
      } else {
        await signIn({
          email: values.email.trim(),
          password: values.password,
        });

        const from = location.state?.from;

        const destination = from
          ? `${from.pathname}${from.search || ""}${from.hash || ""}`
          : "/";

        navigate(destination, { replace: true });
      }
    } catch (requestError) {
      setError(
        requestError.response
          ? getErrorMessage(requestError)
          : requestError.message
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <Link
          className="auth-brand"
          to="/login"
          aria-label="Inventory Desk"
        >
          <span className="auth-brand-icon">
            <Boxes size={22} />
          </span>

          <span>
            <strong>Inventory Desk</strong>
            <small>STOCK CONTROL</small>
          </span>
        </Link>

        <div className="auth-heading">
          <h1>
            {isRegister ? "Create your account" : "Welcome back"}
          </h1>

          <p>
            {isRegister
              ? "Get started with your inventory workspace."
              : "Sign in to your inventory workspace."}
          </p>
        </div>

        {error && (
          <p
            className="auth-feedback auth-feedback-error"
            role="alert"
          >
            {error}
          </p>
        )}

        {message && (
          <p
            className="auth-feedback auth-feedback-success"
            role="status"
          >
            {message}
          </p>
        )}

        {!message && (
          <form className="auth-form" onSubmit={submit}>
            {isRegister && (
              <label className="auth-field" htmlFor="full-name">
                <span>Full name</span>

                <span className="auth-input-wrap">
                  <UserRound size={17} aria-hidden="true" />

                  <input
                    id="full-name"
                    autoComplete="name"
                    value={values.full_name}
                    onChange={update("full_name")}
                    minLength={2}
                    maxLength={100}
                    required
                  />
                </span>
              </label>
            )}

            <label className="auth-field" htmlFor="email">
              <span>Email address</span>

              <span className="auth-input-wrap">
                <Mail size={17} aria-hidden="true" />

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={values.email}
                  onChange={update("email")}
                  maxLength={254}
                  required
                />
              </span>
            </label>

            <PasswordField
              id="password"
              label="Password"
              value={values.password}
              onChange={update("password")}
              autoComplete={
                isRegister ? "new-password" : "current-password"
              }
            />

            {isRegister && (
              <PasswordField
                id="confirm-password"
                label="Confirm password"
                value={values.confirm_password}
                onChange={update("confirm_password")}
                autoComplete="new-password"
              />
            )}

            <button
              className="button button-primary auth-submit"
              type="submit"
              disabled={busy}
            >
              {busy
                ? "Please wait..."
                : isRegister
                  ? "Create account"
                  : "Sign in"}
            </button>
          </form>
        )}

        <nav className="auth-links" aria-label="Account options">
          {isRegister ? (
            <span>
              Already have an account?{" "}
              <Link to="/login">Sign in</Link>
            </span>
          ) : (
            <span>
              New here?{" "}
              <Link to="/register">Create an account</Link>
            </span>
          )}

          {message && isRegister && (
            <Link to="/login">Go to Login</Link>
          )}
        </nav>
      </section>

      <p className="auth-privacy-note">
        Your password is securely hashed by the server and is never
        stored in your browser.
      </p>
    </main>
  );
}
