import { useMemo, useState } from "react";
import { Search, TriangleAlert } from "lucide-react";
import { Card, DataTable, EmptyState, ErrorState, formatQuantity, LoadingState, PageTitle, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";

export default function LowStockPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const { data, loading, error, reload } = useApi("/stock/low");

  const categories = useMemo(
    () => [...new Set((data || []).map((row) => row.category))].sort(),
    [data],
  );
  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (data || []).filter((row) => {
      const matchesSearch = !query || row.item_name.toLowerCase().includes(query) || row.sku.toLowerCase().includes(query);
      return matchesSearch && (!category || row.category === category);
    });
  }, [category, data, search]);

  const columns = [
    { key: "sku", label: "SKU", className: "cell-mono" },
    { key: "item_name", label: "Item" },
    { key: "category", label: "Category" },
    { key: "quantity_on_hand", label: "On hand", render: (row) => formatQuantity(row.quantity_on_hand) },
    { key: "reorder_level", label: "Reorder level", render: (row) => formatQuantity(row.reorder_level) },
    { key: "shortage_quantity", label: "Shortage", render: (row) => formatQuantity(row.shortage_quantity) },
    {
      key: "severity",
      label: "Severity",
      render: (row) => row.quantity_on_hand === 0
        ? <StatusPill tone="danger">Out of stock</StatusPill>
        : <StatusPill tone="warning">Reorder needed</StatusPill>,
    },
  ];

  return (
    <section className="page-section">
      <PageTitle
        title="Low Stock Alerts"
        description="Items whose current quantity is at or below the configured reorder level."
        action={data && <div className="alert-count"><TriangleAlert size={16} /> {formatQuantity(data.length)} items need attention</div>}
      />
      <Card className="table-card">
        <div className="filter-toolbar">
          <label className="search-control">
            <Search size={17} aria-hidden="true" />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name or SKU" aria-label="Search low-stock items" />
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter by category</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="">All categories</option>
              {categories.map((option) => <option key={option} value={option}>{option}</option>)}
            </select>
          </label>
        </div>
        {loading && !data && <LoadingState label="Checking stock levels..." />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && !error && (filtered.length
          ? <DataTable columns={columns} rows={filtered} rowKey={(row) => row.item_id} minWidth={760} />
          : <EmptyState title="All caught up" description={search || category ? "No low-stock items match these filters." : "No items are at or below their reorder level."} />)}
      </Card>
    </section>
  );
}
