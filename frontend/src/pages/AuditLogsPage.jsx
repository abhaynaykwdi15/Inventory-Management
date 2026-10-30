import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { DataTable, EmptyState, ErrorState, formatDate, LoadingState, PageTitle, Pagination, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";

const pageSize = 15;

export default function AuditLogsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [tableName, setTableName] = useState("");
  const [actionType, setActionType] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timeout = window.setTimeout(() => setSearch(searchInput.trim()), 250);
    return () => window.clearTimeout(timeout);
  }, [searchInput]);
  useEffect(() => setPage(1), [search, tableName, actionType]);

  const { data, loading, error, reload } = useApi("/audit-logs", {
    table_name: tableName || undefined,
    action_type: actionType || undefined,
    search: search || undefined,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  });

  const columns = [
    { key: "action_timestamp", label: "Timestamp", render: (row) => formatDate(row.action_timestamp, true) },
    { key: "table_name", label: "Table", className: "cell-mono" },
    { key: "record_id", label: "Record ID" },
    {
      key: "action_type",
      label: "Action",
      render: (row) => <StatusPill tone={row.action_type === "DELETE" ? "danger" : row.action_type === "INSERT" ? "success" : "info"}>{row.action_type}</StatusPill>,
    },
    { key: "changed_by", label: "Database user" },
    { key: "old_value", label: "Previous value", render: (row) => <span className="audit-value" title={row.old_value || ""}>{row.old_value || "—"}</span> },
    { key: "new_value", label: "New value", render: (row) => <span className="audit-value" title={row.new_value || ""}>{row.new_value || "—"}</span> },
  ];

  return (
    <section className="page-section">
      <PageTitle title="Audit Logs" description="Read-only history recorded automatically by MySQL triggers." />
      <section className="card table-card">
        <div className="filter-toolbar filter-toolbar-wrap">
          <label className="search-control">
            <Search size={17} aria-hidden="true" />
            <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search audit entries" aria-label="Search audit entries" />
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter by table</span>
            <select value={tableName} onChange={(event) => setTableName(event.target.value)}>
              <option value="">All tables</option>
              <option value="ITEMS">Items</option>
              <option value="STOCK">Stock</option>
              <option value="STOCK_TRANSACTIONS">Stock transactions</option>
            </select>
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter by action</span>
            <select value={actionType} onChange={(event) => setActionType(event.target.value)}>
              <option value="">All actions</option>
              <option value="INSERT">Insert</option>
              <option value="UPDATE">Update</option>
              <option value="DELETE">Delete</option>
            </select>
          </label>
        </div>
        {loading && !data && <LoadingState label="Loading audit history..." />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && !error && (data.items.length
          ? <DataTable columns={columns} rows={data.items} rowKey={(row) => row.audit_id} minWidth={1080} />
          : <EmptyState title="No audit records found" description="MySQL triggers add audit history when an audited row changes." />)}
        {data && !error && <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />}
      </section>
    </section>
  );
}
