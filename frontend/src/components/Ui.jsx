import { useEffect, useRef } from "react";
import { AlertCircle, ChevronLeft, ChevronRight, LoaderCircle, X } from "lucide-react";

export function PageTitle({ eyebrow = "INVENTORY WORKSPACE", title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action && <div className="page-heading-action">{action}</div>}
    </div>
  );
}

export function Card({ children, className = "", title, subtitle, action }) {
  return (
    <section className={`card ${className}`}>
      {(title || subtitle || action) && (
        <div className="card-heading">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function LoadingState({ label = "Loading inventory data..." }) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={21} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-panel state-error" role="alert">
      <AlertCircle size={21} aria-hidden="true" />
      <span>{message}</span>
      {onRetry && <button className="button button-secondary button-small" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function EmptyState({ title = "No records found", description = "There is no data to display yet." }) {
  return (
    <div className="state-panel state-empty">
      <span className="empty-mark" aria-hidden="true">—</span>
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  );
}

export function Pagination({ page, pageSize, total, onPageChange }) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="pagination">
      <span>
        {total === 0 ? "No records" : `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}`}
      </span>
      <div className="pagination-actions">
        <button
          className="icon-button"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={17} />
        </button>
        <span>Page {page} of {pageCount}</span>
        <button
          className="icon-button"
          aria-label="Next page"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={17} />
        </button>
      </div>
    </div>
  );
}

export function DataTable({ columns, rows, rowKey, minWidth = 720 }) {
  if (rows.length === 0) return null;
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable table">
      <table style={{ minWidth }}>
        <thead>
          <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td key={column.key} className={column.className || ""}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Field({ label, id, error, children, className = "" }) {
  return (
    <label className={`form-field ${className}`} htmlFor={id}>
      <span>{label}</span>
      {children}
      {error && <small className="field-error">{error}</small>}
    </label>
  );
}

export function Feedback({ kind = "success", children }) {
  return (
    <p className={`feedback feedback-${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </p>
  );
}

export function Modal({ title, onClose, children }) {
  const closeButton = useRef(null);

  useEffect(() => {
    closeButton.current?.focus();
    const closeOnEscape = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button ref={closeButton} className="icon-button" aria-label="Close dialog" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}

export function StatusPill({ children, tone = "neutral" }) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}

export function formatDate(value, withTime = false) {
  if (!value) return "Never";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, withTime
    ? { dateStyle: "medium", timeStyle: "short" }
    : { dateStyle: "medium" }).format(date);
}

export function formatQuantity(value) {
  return new Intl.NumberFormat().format(Number(value || 0));
}

export function formatCurrency(value) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(Number(value || 0));
}
