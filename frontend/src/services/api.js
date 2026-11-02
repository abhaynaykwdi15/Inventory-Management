import axios from "axios";

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const missingProductionApiBaseUrl = import.meta.env.PROD && !configuredApiBaseUrl;
const apiBaseUrl = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/+$/, "")
  : "/api";

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

const API_BASE_URL_CONFIGURATION_ERROR =
  "VITE_API_BASE_URL is missing. Set it to the production backend API URL in Vercel and redeploy.";

api.interceptors.request.use((config) => {
  if (missingProductionApiBaseUrl) {
    return Promise.reject(new Error(API_BASE_URL_CONFIGURATION_ERROR));
  }
  return config;
});

export function getErrorMessage(error) {
  if (error?.message === API_BASE_URL_CONFIGURATION_ERROR) {
    return API_BASE_URL_CONFIGURATION_ERROR;
  }
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
