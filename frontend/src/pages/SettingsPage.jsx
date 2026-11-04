
import { useState } from "react";
import { Database, KeyRound, Server, UserRound } from "lucide-react";
import {
  Card,
  ErrorState,
  Feedback,
  Field,
  LoadingState,
  PageTitle,
  StatusPill,
} from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";
import { api, getErrorMessage } from "../services/api.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function SettingsPage() {
  const { user, setUser } = useAuth();

  const [profile, setProfile] = useState({
    full_name: user.full_name,
    email: user.email,
  });

  const [password, setPassword] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [profileBusy, setProfileBusy] = useState(false);
  const [passwordBusy, setPasswordBusy] = useState(false);

  const [profileMessage, setProfileMessage] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");

  const [profileError, setProfileError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const apiStatus = useApi("/status");
  const databaseStatus = useApi("/health");

  const loading = apiStatus.loading || databaseStatus.loading;

  const reload = () =>
    Promise.all([apiStatus.reload(), databaseStatus.reload()]);

  const saveProfile = async (event) => {
    event.preventDefault();

    setProfileBusy(true);
    setProfileError("");
    setProfileMessage("");

    try {
      const { data } = await api.put("/auth/profile", profile);

      setUser(data);

      setProfile({
        full_name: data.full_name,
        email: data.email,
      });

      setProfileMessage("Your profile has been updated.");
    } catch (error) {
      setProfileError(getErrorMessage(error));
    } finally {
      setProfileBusy(false);
    }
  };

  const changePassword = async (event) => {
    event.preventDefault();

    setPasswordError("");
    setPasswordMessage("");

    if (password.new_password !== password.confirm_password) {
      setPasswordError("The new passwords do not match.");
      return;
    }

    setPasswordBusy(true);

    try {
      const { data } = await api.post("/auth/change-password", {
        current_password: password.current_password,
        new_password: password.new_password,
      });

      setPasswordMessage(data.message);

      setPassword({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error) {
      setPasswordError(getErrorMessage(error));
    } finally {
      setPasswordBusy(false);
    }
  };

  return (
    <section className="page-section">
      <PageTitle
        title="Settings"
        description="Manage your account, security, and service connections."
      />

      <div className="settings-account-grid">
        <Card
          title="Account profile"
          subtitle="Manage your account details."
        >
          <div className="account-summary">
            <div className="setting-icon">
              <UserRound size={19} />
            </div>

            <div className="setting-copy">
              <strong>{user.full_name}</strong>
              <span>{user.email}</span>
            </div>
          </div>

          {profileError && (
            <Feedback kind="error">{profileError}</Feedback>
          )}

          {profileMessage && (
            <Feedback>{profileMessage}</Feedback>
          )}

          <form className="account-form" onSubmit={saveProfile}>
            <Field label="Full name" id="settings-full-name">
              <input
                id="settings-full-name"
                autoComplete="name"
                minLength="2"
                maxLength="100"
                required
                value={profile.full_name}
                onChange={(event) =>
                  setProfile((current) => ({
                    ...current,
                    full_name: event.target.value,
                  }))
                }
              />
            </Field>

            <Field label="Login email address" id="settings-email">
              <input
                id="settings-email"
                type="email"
                autoComplete="email"
                maxLength="254"
                required
                value={profile.email}
                onChange={(event) =>
                  setProfile((current) => ({
                    ...current,
                    email: event.target.value,
                  }))
                }
              />
            </Field>

            <button
              className="button button-primary"
              type="submit"
              disabled={profileBusy}
            >
              {profileBusy ? "Saving..." : "Save profile"}
            </button>
          </form>
        </Card>

        <Card
          title="Password & security"
          subtitle="Change your account password."
        >
          {passwordError && (
            <Feedback kind="error">{passwordError}</Feedback>
          )}

          {passwordMessage && (
            <Feedback>{passwordMessage}</Feedback>
          )}

          <form className="account-form" onSubmit={changePassword}>
            <Field label="Current password" id="current-password">
              <input
                id="current-password"
                type="password"
                autoComplete="current-password"
                required
                maxLength="128"
                value={password.current_password}
                onChange={(event) =>
                  setPassword((current) => ({
                    ...current,
                    current_password: event.target.value,
                  }))
                }
              />
            </Field>

            <Field
              label="New password (at least 12 characters)"
              id="new-password"
            >
              <input
                id="new-password"
                type="password"
                autoComplete="new-password"
                required
                minLength="12"
                maxLength="128"
                value={password.new_password}
                onChange={(event) =>
                  setPassword((current) => ({
                    ...current,
                    new_password: event.target.value,
                  }))
                }
              />
            </Field>

            <Field
              label="Confirm new password"
              id="confirm-new-password"
            >
              <input
                id="confirm-new-password"
                type="password"
                autoComplete="new-password"
                required
                minLength="12"
                maxLength="128"
                value={password.confirm_password}
                onChange={(event) =>
                  setPassword((current) => ({
                    ...current,
                    confirm_password: event.target.value,
                  }))
                }
              />
            </Field>

            <button
              className="button button-secondary"
              type="submit"
              disabled={passwordBusy}
            >
              <KeyRound size={16} />
              {passwordBusy ? "Updating..." : "Change password"}
            </button>
          </form>
        </Card>
      </div>

      <div className="settings-grid">
        <Card title="API service" subtitle="FastAPI backend">
          <div className="setting-row">
            <div className="setting-icon">
              <Server size={18} />
            </div>

            <div className="setting-copy">
              <strong>Inventory API</strong>
              <span>
                Configured through the frontend API base URL.
              </span>
            </div>

            {apiStatus.error ? (
              <StatusPill tone="danger">Unavailable</StatusPill>
            ) : apiStatus.data ? (
              <StatusPill tone="success">Connected</StatusPill>
            ) : (
              <StatusPill tone="neutral">Checking</StatusPill>
            )}
          </div>
        </Card>

        <Card title="MySQL database" subtitle="Database-backed mode">
          <div className="setting-row">
            <div className="setting-icon">
              <Database size={18} />
            </div>

            <div className="setting-copy">
              <strong>MySQL</strong>
              <span>
                Connection pool and credentials are configured on the backend.
              </span>
            </div>

            {databaseStatus.error ? (
              <StatusPill tone="danger">Unavailable</StatusPill>
            ) : databaseStatus.data ? (
              <StatusPill tone="success">Connected</StatusPill>
            ) : (
              <StatusPill tone="neutral">Checking</StatusPill>
            )}
          </div>
        </Card>
      </div>

      {loading && (
        <LoadingState label="Checking backend and MySQL status..." />
      )}

      {databaseStatus.error && (
        <ErrorState
          message={databaseStatus.error}
          onRetry={reload}
        />
      )}

      {apiStatus.error && !databaseStatus.error && (
        <ErrorState
          message={apiStatus.error}
          onRetry={reload}
        />
      )}

      <p className="settings-note">
        All registered users share this inventory workspace.
        Account passwords and sessions are managed by the backend.
        SMTP and database credentials must remain in backend environment settings.
      </p>
    </section>
  );
}
