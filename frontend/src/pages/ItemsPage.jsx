import { useCallback, useEffect, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useLocation } from "react-router-dom";
import { DataTable, EmptyState, ErrorState, Field, Feedback, formatCurrency, formatQuantity, LoadingState, Modal, PageTitle, Pagination, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";
import { api, getErrorMessage } from "../services/api.js";

const pageSize = 10;
const emptyForm = {
  sku: "",
  item_name: "",
  category: "",
  description: "",
  unit_price: "",
  reorder_level: "",
};

function stockStatus(item) {
  if (item.quantity_on_hand === 0) return <StatusPill tone="danger">Out of stock</StatusPill>;
  if (item.quantity_on_hand <= item.reorder_level) return <StatusPill tone="warning">Low stock</StatusPill>;
  return <StatusPill tone="success">Healthy</StatusPill>;
}

export default function ItemsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sortBy, setSortBy] = useState("item_name");
  const [direction, setDirection] = useState("asc");
  const [page, setPage] = useState(1);
  const [editingItem, setEditingItem] = useState(null);
  const [deletingItem, setDeletingItem] = useState(null);
  const [formValues, setFormValues] = useState(emptyForm);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");
  const location = useLocation();

  useEffect(() => {
    const timeout = window.setTimeout(() => setSearch(searchInput.trim()), 250);
    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  useEffect(() => {
    const query = new URLSearchParams(location.search).get("search") || "";
    setSearchInput(query);
    setSearch(query.trim());
  }, [location.search]);

  useEffect(() => setPage(1), [search, category, sortBy, direction]);

  const query = {
    search: search || undefined,
    category: category || undefined,
    sort_by: sortBy,
    direction,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };
  const { data, loading, error, reload } = useApi("/items", query);
  const categories = useApi("/items/categories");

  const closeForm = useCallback(() => setEditingItem(null), []);
  const closeDelete = useCallback(() => setDeletingItem(null), []);
  const openForm = (item = null) => {
    setEditingItem(item || true);
    setFormValues(item ? {
      sku: item.sku,
      item_name: item.item_name,
      category: item.category,
      description: item.description || "",
      unit_price: String(item.unit_price),
      reorder_level: String(item.reorder_level),
    } : emptyForm);
    setFormError("");
  };

  const submitItem = async (event) => {
    event.preventDefault();
    setBusy(true);
    setFormError("");
    const payload = {
      ...formValues,
      unit_price: Number(formValues.unit_price),
      reorder_level: Number(formValues.reorder_level),
    };
    try {
      if (editingItem !== true) {
        await api.put(`/items/${editingItem.item_id}`, payload);
      } else {
        await api.post("/items", payload);
      }
      await Promise.all([reload(), categories.reload()]);
      setEditingItem(null);
      setNotice(editingItem === true ? "Item created successfully." : "Item updated successfully.");
    } catch (requestError) {
      setFormError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = async () => {
    if (!deletingItem) return;
    setBusy(true);
    setFormError("");
    try {
      await api.delete(`/items/${deletingItem.item_id}`);
      await Promise.all([reload(), categories.reload()]);
      setNotice(`${deletingItem.item_name} deleted.`);
      setDeletingItem(null);
    } catch (requestError) {
      setFormError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const toggleSort = (field) => {
    if (field === sortBy) {
      setDirection((current) => current === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setDirection("asc");
    }
  };

  const columns = [
    { key: "sku", label: "SKU", className: "cell-mono" },
    { key: "item_name", label: "Item" },
    { key: "category", label: "Category" },
    { key: "unit_price", label: "Unit price", render: (row) => formatCurrency(row.unit_price) },
    { key: "quantity_on_hand", label: "On hand", render: (row) => formatQuantity(row.quantity_on_hand) },
    { key: "reorder_level", label: "Reorder at", render: (row) => formatQuantity(row.reorder_level) },
    { key: "status", label: "Status", render: stockStatus },
    {
      key: "actions",
      label: "Actions",
      render: (row) => (
        <div className="table-actions">
          <button className="icon-button" aria-label={`Edit ${row.item_name}`} onClick={() => openForm(row)}><Pencil size={16} /></button>
          <button className="icon-button icon-danger" aria-label={`Delete ${row.item_name}`} onClick={() => { setFormError(""); setDeletingItem(row); }}><Trash2 size={16} /></button>
        </div>
      ),
    },
  ];

  return (
    <section className="page-section">
      <PageTitle
        title="Items"
        description="Manage the catalog, prices, categories, and reorder levels."
        action={<button className="button button-primary" onClick={() => openForm()}><Plus size={17} /> Add item</button>}
      />
      {notice && <Feedback>{notice}</Feedback>}
      <section className="card table-card">
        <div className="filter-toolbar">
          <label className="search-control">
            <Search size={17} aria-hidden="true" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search name or SKU"
              aria-label="Search items by name or SKU"
            />
          </label>
          <label className="filter-control">
            <span className="sr-only">Filter by category</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="">All categories</option>
              {(categories.data || []).map((option) => <option key={option} value={option}>{option}</option>)}
            </select>
          </label>
          <label className="filter-control">
            <span className="sr-only">Sort items</span>
            <select value={sortBy} onChange={(event) => toggleSort(event.target.value)}>
              <option value="item_name">Sort: Item name</option>
              <option value="sku">Sort: SKU</option>
              <option value="category">Sort: Category</option>
              <option value="unit_price">Sort: Price</option>
              <option value="quantity_on_hand">Sort: Quantity</option>
            </select>
          </label>
          <button className="button button-secondary button-sort" onClick={() => setDirection((value) => value === "asc" ? "desc" : "asc")} aria-label={`Sort ${direction === "asc" ? "descending" : "ascending"}`}>
            {direction === "asc" ? "Ascending" : "Descending"}
          </button>
        </div>

        {loading && !data && <LoadingState label="Loading items..." />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && !error && (
          data.items.length ? (
            <DataTable columns={columns} rows={data.items} rowKey={(row) => row.item_id} minWidth={960} />
          ) : (
            <EmptyState title="No items match" description="Try a different search or add a fictional sample item." />
          )
        )}
        {data && !error && <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />}
      </section>

      {editingItem !== null && (
        <Modal title={editingItem === true ? "Add inventory item" : "Edit inventory item"} onClose={closeForm}>
          <form className="form-grid" onSubmit={submitItem}>
            {formError && <Feedback kind="error">{formError}</Feedback>}
            <Field label="SKU" id="item-sku">
              <input id="item-sku" name="sku" maxLength="40" required value={formValues.sku} onChange={(event) => setFormValues({ ...formValues, sku: event.target.value })} />
            </Field>
            <Field label="Item name" id="item-name">
              <input id="item-name" name="item_name" maxLength="150" required value={formValues.item_name} onChange={(event) => setFormValues({ ...formValues, item_name: event.target.value })} />
            </Field>
            <Field label="Category" id="item-category">
              <input id="item-category" name="category" maxLength="80" required list="item-categories" value={formValues.category} onChange={(event) => setFormValues({ ...formValues, category: event.target.value })} />
              <datalist id="item-categories">{(categories.data || []).map((option) => <option key={option} value={option} />)}</datalist>
            </Field>
            <Field label="Unit price (USD)" id="item-price">
              <input id="item-price" name="unit_price" type="number" min="0" step="0.01" required value={formValues.unit_price} onChange={(event) => setFormValues({ ...formValues, unit_price: event.target.value })} />
            </Field>
            <Field label="Reorder level" id="item-reorder">
              <input id="item-reorder" name="reorder_level" type="number" min="0" step="1" required value={formValues.reorder_level} onChange={(event) => setFormValues({ ...formValues, reorder_level: event.target.value })} />
            </Field>
            <Field label="Description (optional)" id="item-description" className="form-field-wide">
              <textarea id="item-description" name="description" maxLength="1000" rows="3" value={formValues.description} onChange={(event) => setFormValues({ ...formValues, description: event.target.value })} />
            </Field>
            <div className="modal-actions form-field-wide">
              <button type="button" className="button button-secondary" onClick={closeForm}>Cancel</button>
              <button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving..." : "Save item"}</button>
            </div>
          </form>
        </Modal>
      )}

      {deletingItem && (
        <Modal title="Delete item?" onClose={closeDelete}>
          <div className="confirm-content">
            <p>Delete <strong>{deletingItem.item_name}</strong> ({deletingItem.sku})?</p>
            <p className="muted-text">Items with transaction history cannot be deleted. This action cannot be undone.</p>
            {formError && <Feedback kind="error">{formError}</Feedback>}
            <div className="modal-actions">
              <button className="button button-secondary" onClick={closeDelete} disabled={busy}>Cancel</button>
              <button className="button button-danger" onClick={confirmDelete} disabled={busy}>{busy ? "Deleting..." : "Delete item"}</button>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}
