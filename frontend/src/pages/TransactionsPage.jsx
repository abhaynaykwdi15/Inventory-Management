import { useEffect, useState } from "react";
import { DataTable, EmptyState, ErrorState, formatDate, formatQuantity, LoadingState, PageTitle, Pagination, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";

const pageSize = 15;

export default function TransactionsPage() {
  const [type, setType] = useState("");
  const [itemId, setItemId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const dateRangeInvalid = Boolean(dateFrom && dateTo && dateFrom > dateTo);
  const items = useApi("/items", { limit: 100, offset: 0, sort_by: "item_name", direction: "asc" });
  const transactions = useApi("/transactions", {
    transaction_type: type || undefined,
    item_id: itemId ? Number(itemId) : undefined,
    date_from: dateRangeInvalid ? undefined : dateFrom || undefined,
    date_to: dateRangeInvalid ? undefined : dateTo || undefined,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  });

  useEffect(() => setPage(1), [type, itemId, dateFrom, dateTo]);

  const columns = [
    { key: "transaction_id", label: "Transaction", render: (row) => `#${row.transaction_id}` },
    { key: "transaction_date", label: "Date and time", render: (row) => formatDate(row.transaction_date, true) },
    {
      key: "item_name",
      label: "Item",
      render: (row) => <div className="item-cell"><strong>{row.item_name}</strong><span>{row.sku}</span></div>,
    },
    {
      key: "transaction_type",
      label: "Type",
      render: (row) => <StatusPill tone={row.transaction_type === "IN" ? "success" : "info"}>{row.transaction_type}</StatusPill>,
    },
    { key: "quantity", label: "Quantity", render: (row) => formatQuantity(row.quantity) },
    { key: "remarks", label: "Remarks", render: (row) => row.remarks || "—" },
    { key: "created_by", label: "Recorded by" },
  ];

  const resetFilters = () => {
    setType("");
    setItemId("");
    setDateFrom("");
    setDateTo("");
  };

  const error = transactions.error || items.error;
  return (
    <section className="page-section">
      <PageTitle title="Stock Transactions" description="Search and review recorded stock receipts and issues." />
      <section className="card table-card">
        <div className="filter-toolbar filter-toolbar-wrap">
          <label className="filter-control">
            <span className="sr-only">Transaction type</span>
            <select value={type} onChange={(event) => setType(event.target.value)}>
              <option value="">All types</option>
              <option value="IN">Stock in</option>
              <option value="OUT">Stock out</option>
            </select>
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter by item</span>
            <select value={itemId} onChange={(event) => setItemId(event.target.value)}>
              <option value="">All items</option>
              {(items.data?.items || []).map((item) => <option key={item.item_id} value={item.item_id}>{item.item_name}</option>)}
            </select>
          </label>
          <label className="filter-control filter-date">
            <span>From</span>
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} aria-label="Filter transactions from date" />
          </label>
          <label className="filter-control filter-date">
            <span>To</span>
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} aria-label="Filter transactions to date" />
          </label>
          {(type || itemId || dateFrom || dateTo) && <button className="button button-quiet button-small" onClick={resetFilters}>Clear filters</button>}
        </div>
        {dateRangeInvalid && <p className="filter-warning">The start date must be on or before the end date.</p>}
        {loadingWithNoData(transactions.loading, transactions.data) && <LoadingState label="Loading transactions..." />}
        {error && <ErrorState message={error} onRetry={() => { void transactions.reload(); void items.reload(); }} />}
        {transactions.data && !error && !dateRangeInvalid && (
          transactions.data.items.length
            ? <DataTable columns={columns} rows={transactions.data.items} rowKey={(row) => row.transaction_id} minWidth={900} />
            : <EmptyState title="No transactions found" description="Try changing the filters or record a stock movement." />
        )}
        {transactions.data && <Pagination page={page} pageSize={pageSize} total={transactions.data.total} onPageChange={setPage} />}
      </section>
    </section>
  );
}

function loadingWithNoData(loading, data) {
  return loading && !data;
}
