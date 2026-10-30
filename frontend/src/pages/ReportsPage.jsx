import { useEffect, useState } from "react";
import { Download, Search } from "lucide-react";
import { DataTable, EmptyState, ErrorState, formatDate, formatQuantity, LoadingState, PageTitle, Pagination, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";
import { api, getErrorMessage } from "../services/api.js";

const pageSize = 10;

function csvValue(value) {
  let text = value == null ? "" : String(value);
  if (/^[\s]*[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

function saveCsv(filename, headers, rows) {
  const lines = [headers, ...rows];
  const content = `\uFEFF${lines.map((line) => line.map(csvValue).join(",")).join("\r\n")}`;
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function ReportTabs({ activeReport, onSelect }) {
  return (
    <div className="reports-tabs" role="tablist" aria-label="Inventory reports">
      <button
        className={`reports-tab${activeReport === "current-stock" ? " reports-tab-active" : ""}`}
        id="current-stock-tab"
        type="button"
        role="tab"
        aria-selected={activeReport === "current-stock"}
        aria-controls="reports-panel"
        onClick={() => onSelect("current-stock")}
      >
        Current stock
      </button>
      <button
        className={`reports-tab${activeReport === "slow-moving" ? " reports-tab-active" : ""}`}
        id="slow-moving-tab"
        type="button"
        role="tab"
        aria-selected={activeReport === "slow-moving"}
        aria-controls="reports-panel"
        onClick={() => onSelect("slow-moving")}
      >
        Slow-moving stock
      </button>
    </div>
  );
}

function CurrentStockReport() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [itemId, setItemId] = useState("");
  const [sortBy, setSortBy] = useState("item_name");
  const [direction, setDirection] = useState("asc");
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    const timeout = window.setTimeout(() => setSearch(searchInput.trim()), 250);
    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  useEffect(() => setPage(1), [search, category, itemId, sortBy, direction]);

  const categories = useApi("/items/categories");
  const itemOptions = useApi("/reports/current-stock/items", {
    category: category || undefined,
  });
  const query = {
    search: search || undefined,
    category: category || undefined,
    item_id: itemId ? Number(itemId) : undefined,
    sort_by: sortBy,
    direction,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };
  const { data, loading, error, reload } = useApi("/reports/current-stock", query);

  const exportCsv = async () => {
    setExporting(true);
    setExportError("");
    try {
      const rows = [];
      let total = data?.total ?? 0;
      let offset = 0;
      while (offset < total) {
        const response = await api.get("/reports/current-stock", {
          params: { ...query, limit: 100, offset },
        });
        const batch = response.data.items;
        if (batch.length === 0) {
          throw new Error("The stock report changed while exporting. Please try again.");
        }
        rows.push(...batch);
        offset += batch.length;
        total = response.data.total;
      }
      saveCsv(
        "current-stock-report.csv",
        ["SKU", "Item", "Category", "Quantity on hand", "Reorder level", "Status", "Last updated"],
        rows.map((row) => [
          row.sku,
          row.item_name,
          row.category,
          row.quantity_on_hand,
          row.reorder_level,
          row.quantity_on_hand === 0
            ? "Out of stock"
            : row.quantity_on_hand <= row.reorder_level
              ? "Low stock"
              : "Healthy",
          row.updated_at ? formatDate(row.updated_at, true) : "",
        ]),
      );
    } catch (requestError) {
      setExportError(
        requestError.response ? getErrorMessage(requestError) : requestError.message,
      );
    } finally {
      setExporting(false);
    }
  };

  const columns = [
    { key: "sku", label: "SKU", className: "cell-mono" },
    { key: "item_name", label: "Item" },
    { key: "category", label: "Category" },
    {
      key: "quantity_on_hand",
      label: "On hand",
      render: (row) => formatQuantity(row.quantity_on_hand),
    },
    {
      key: "reorder_level",
      label: "Reorder at",
      render: (row) => formatQuantity(row.reorder_level),
    },
    {
      key: "status",
      label: "Status",
      render: (row) => row.quantity_on_hand === 0
        ? <StatusPill tone="danger">Out of stock</StatusPill>
        : row.quantity_on_hand <= row.reorder_level
          ? <StatusPill tone="warning">Low stock</StatusPill>
          : <StatusPill tone="success">Healthy</StatusPill>,
    },
    {
      key: "updated_at",
      label: "Last updated",
      render: (row) => formatDate(row.updated_at, true),
    },
  ];

  return (
    <>
      {data && !error && (
        <section className="metrics-grid report-metrics-grid" aria-label="Current stock summary">
          <article className="card metric-card">
            <span className="metric-accent metric-accent-blue" />
            <p>Items in report</p>
            <strong>{formatQuantity(data.summary.total_items)}</strong>
            <span className="metric-note">Matching catalog items</span>
          </article>
          <article className="card metric-card">
            <span className="metric-accent metric-accent-green" />
            <p>Total units</p>
            <strong>{formatQuantity(data.summary.total_units)}</strong>
            <span className="metric-note">On-hand quantity for matching items</span>
          </article>
          <article className="card metric-card">
            <span className="metric-accent metric-accent-orange" />
            <p>Low stock</p>
            <strong>{formatQuantity(data.summary.low_stock_items)}</strong>
            <span className="metric-note">At or below reorder level</span>
          </article>
          <article className="card metric-card">
            <span className="metric-accent metric-accent-red" />
            <p>Out of stock</p>
            <strong>{formatQuantity(data.summary.out_of_stock_items)}</strong>
            <span className="metric-note">Zero units on hand</span>
          </article>
        </section>
      )}

      <section className="card table-card">
        <div className="filter-toolbar filter-toolbar-wrap">
          <label className="search-control">
            <Search size={17} aria-hidden="true" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search item name or SKU"
              aria-label="Search current stock by item name or SKU"
            />
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter current stock by category</span>
            <select
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                setItemId("");
              }}
            >
              <option value="">All categories</option>
              {(categories.data || []).map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter current stock by item</span>
            <select value={itemId} onChange={(event) => setItemId(event.target.value)}>
              <option value="">All items</option>
              {(itemOptions.data || []).map((item) => (
                <option key={item.item_id} value={item.item_id}>
                  {item.item_name} ({item.sku})
                </option>
              ))}
            </select>
          </label>
          <label className="filter-control">
            <span className="sr-only">Sort current stock report</span>
            <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="item_name">Sort: Item name</option>
              <option value="sku">Sort: SKU</option>
              <option value="category">Sort: Category</option>
              <option value="quantity_on_hand">Sort: Quantity</option>
              <option value="reorder_level">Sort: Reorder level</option>
              <option value="updated_at">Sort: Last updated</option>
            </select>
          </label>
          <button
            className="button button-secondary button-sort"
            type="button"
            onClick={() => setDirection((value) => value === "asc" ? "desc" : "asc")}
            aria-label={`Sort ${direction === "asc" ? "descending" : "ascending"}`}
          >
            {direction === "asc" ? "Ascending" : "Descending"}
          </button>
        </div>
        <div className="report-toolbar">
          <p>{data ? `${formatQuantity(data.total)} matching items` : " "}</p>
          <button
            className="button button-secondary"
            disabled={!data?.total || exporting}
            onClick={exportCsv}
          >
            <Download size={16} /> {exporting ? "Exporting..." : "Export CSV"}
          </button>
        </div>
        {exportError && <p className="filter-warning" role="alert">{exportError}</p>}
        {loading && !data && <LoadingState label="Building the current stock report..." />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && !error && (
          data.items.length
            ? <DataTable columns={columns} rows={data.items} rowKey={(row) => row.item_id} minWidth={900} />
            : <EmptyState
              title="No stock items match"
              description="Try changing the search or filters to see current stock."
            />
        )}
        {data && !error && (
          <Pagination
            page={page}
            pageSize={pageSize}
            total={data.total}
            onPageChange={setPage}
          />
        )}
      </section>
    </>
  );
}

function SlowMovingReport({ days, setDays }) {
  const { data, loading, error, reload } = useApi("/reports/slow-moving", { days });
  const columns = [
    { key: "item_name", label: "Item" },
    { key: "sku", label: "SKU", className: "cell-mono" },
    { key: "category", label: "Category" },
    { key: "quantity_on_hand", label: "Current stock", render: (row) => formatQuantity(row.quantity_on_hand) },
    { key: "last_issue_date", label: "Last issue", render: (row) => formatDate(row.last_issue_date) },
    { key: "days_since_last_issue", label: "Days inactive", render: (row) => row.days_since_last_issue == null ? "—" : `${formatQuantity(row.days_since_last_issue)} days` },
    {
      key: "report_status",
      label: "Status",
      render: (row) => row.report_status === "NEVER_ISSUED"
        ? <StatusPill tone="neutral">Never issued</StatusPill>
        : <StatusPill tone="warning">Inactive</StatusPill>,
    },
  ];

  return (
    <section className="card table-card">
      <div className="report-toolbar">
        <p>{data ? `${formatQuantity(data.length)} matching items` : " "}</p>
        <button className="button button-secondary" disabled={!data?.length} onClick={() => {
          saveCsv(
            "slow-moving-inventory.csv",
            ["Item", "SKU", "Category", "Current stock", "Last issue date", "Days since issue", "Status"],
            (data || []).map((row) => [
              row.item_name,
              row.sku,
              row.category,
              row.quantity_on_hand,
              row.last_issue_date ? formatDate(row.last_issue_date) : "Never",
              row.days_since_last_issue ?? "",
              row.report_status,
            ]),
          );
        }}>
          <Download size={16} /> Export CSV
        </button>
      </div>
      {loading && !data && <LoadingState label="Building the slow-moving report..." />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && !error && (data.length
        ? <DataTable columns={columns} rows={data} rowKey={(row) => row.item_id} minWidth={880} />
        : <EmptyState title="No slow-moving items" description={`Every item has had an issue within the last ${days} days.`} />)}
    </section>
  );
}

export default function ReportsPage() {
  const [activeReport, setActiveReport] = useState("current-stock");
  const [days, setDays] = useState(30);

  return (
    <section className="page-section">
      <PageTitle
        title={activeReport === "current-stock" ? "Current stock report" : "Slow-moving stock"}
        description={activeReport === "current-stock"
          ? "Review current quantities, stock health, and item-level balances from your inventory."
          : "Items with no issue history or no stock issue during the selected inactivity period."}
        action={activeReport === "slow-moving" && (
          <label className="period-control">
            <span>Inactivity period</span>
            <select
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
              aria-label="Slow-moving inactivity period"
            >
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </label>
        )}
      />
      <ReportTabs activeReport={activeReport} onSelect={setActiveReport} />
      <div
        id="reports-panel"
        role="tabpanel"
        aria-labelledby={activeReport === "current-stock" ? "current-stock-tab" : "slow-moving-tab"}
      >
        {activeReport === "current-stock"
          ? <CurrentStockReport />
          : <SlowMovingReport days={days} setDays={setDays} />}
      </div>
    </section>
  );
}
