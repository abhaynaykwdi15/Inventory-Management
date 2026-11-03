import axios from "axios";

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

// Automatically append /api so all endpoints align with backend routers
const apiBaseUrl = configuredApiBaseUrl
  ? `${configuredApiBaseUrl.replace(/\/+$/, "")}/api`
  : "/api";

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 45000,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((entry) => entry.msg).filter(Boolean).join(" ");
  }
  if (error?.code === "ECONNABORTED") {
    return "The API request timed out. Check that the backend is running.";
  }
  if (!error?.response) {
    return "The API could not be reached. Check the backend and its MySQL connection.";
  }
  return "The request could not be completed.";
}
