import { useCallback, useEffect, useRef, useState } from "react";
import { api, getErrorMessage } from "../services/api.js";

export function useApi(path, params = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestNumber = useRef(0);
  const paramsKey = JSON.stringify(params);

  const reload = useCallback(async () => {
    const requestId = ++requestNumber.current;
    setLoading(true);
    setError("");
    try {
      const response = await api.get(path, { params: JSON.parse(paramsKey) });
      if (requestId === requestNumber.current) {
        setData(response.data);
        setLoading(false);
      }
      return response.data;
    } catch (requestError) {
      if (requestId === requestNumber.current) {
        setError(getErrorMessage(requestError));
        setLoading(false);
      }
      return null;
    }
  }, [path, paramsKey]);

  useEffect(() => {
    void reload();
    return () => {
      requestNumber.current += 1;
    };
  }, [reload]);

  return { data, loading, error, reload };
}
