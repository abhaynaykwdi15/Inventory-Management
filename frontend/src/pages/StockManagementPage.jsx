import { useMemo, useState } from "react";
import { ArrowDownToLine, ArrowUpFromLine, Boxes } from "lucide-react";
import { Card, EmptyState, ErrorState, Field, Feedback, formatQuantity, LoadingState, PageTitle, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";
import { api, getErrorMessage } from "../services/api.js";

export default function StockManagementPage() {
  const [movementType, setMovementType] = useState("IN");
  const [itemId, setItemId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [remarks, setRemarks] = useState("");
  const [createdBy, setCreatedBy] = useState("demo-user");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const items = useApi("/items", { limit: 100, offset: 0, sort_by: "item_name", direction: "asc" });
  const stock = useApi("/stock");

  const selectedStock = useMemo(
    () => (stock.data || []).find((row) => String(row.item_id) === itemId),
    [itemId, stock.data],
  );
  const available = selectedStock?.quantity_on_hand ?? 0;
  const amount = Number(quantity);
  const exceedsAvailable = movementType === "OUT" && amount > available;
  const expectedQuantity = movementType === "IN" ? available + (amount || 0) : available - (amount || 0);

  const submitMovement = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    setErrorMessage("");
    try {
      const result = await api.post(`/stock/${movementType.toLowerCase()}`, {
        item_id: Number(itemId),
        quantity: Number(quantity),
        remarks: remarks.trim() || null,
        created_by: createdBy.trim(),
      });
      setMessage(`${result.data.message} Current stock: ${formatQuantity(result.data.quantity_on_hand)} units.`);
      setQuantity("");
      setRemarks("");
      await stock.reload();
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const loading = items.loading || stock.loading;
  const requestError = items.error || stock.error;

  return (
    <section className="page-section">
      <PageTitle title="Stock Management" description="Record inventory receipts and issues. The server is authoritative for every balance update." />
      {requestError && <ErrorState message={requestError} onRetry={() => { void items.reload(); void stock.reload(); }} />}
      {loading && !items.data && <LoadingState label="Loading item and stock balances..." />}
      {items.data && stock.data && (
        <>
          <div className="stock-layout">
            <Card className="stock-form-card">
              <div className="movement-tabs" role="group" aria-label="Stock movement type">
                <button
                  aria-pressed={movementType === "IN"}
                  className={movementType === "IN" ? "movement-tab active" : "movement-tab"}
                  onClick={() => { setMovementType("IN"); setMessage(""); setErrorMessage(""); }}
                >
                  <ArrowDownToLine size={17} /> Stock In
                </button>
                <button
                  aria-pressed={movementType === "OUT"}
                  className={movementType === "OUT" ? "movement-tab active" : "movement-tab"}
                  onClick={() => { setMovementType("OUT"); setMessage(""); setErrorMessage(""); }}
                >
                  <ArrowUpFromLine size={17} /> Stock Out
                </button>
              </div>
              <div className="movement-intro">
                <div className={`movement-icon ${movementType === "IN" ? "movement-in" : "movement-out"}`}>
                  {movementType === "IN" ? <ArrowDownToLine size={19} /> : <ArrowUpFromLine size={19} />}
                </div>
                <div>
                  <h2>{movementType === "IN" ? "Receive stock" : "Issue stock"}</h2>
                  <p>{movementType === "IN" ? "Add received units to the selected item." : "Remove units from available stock."}</p>
                </div>
              </div>

              <form className="stock-form" onSubmit={submitMovement}>
                <Field label="Inventory item" id="movement-item">
                  <select id="movement-item" required value={itemId} onChange={(event) => setItemId(event.target.value)}>
                    <option value="">Choose an item</option>
                    {items.data.items.map((item) => (
                      <option key={item.item_id} value={item.item_id}>{item.item_name} · {item.sku}</option>
                    ))}
                  </select>
                </Field>
                <div className="available-row">
                  <span>Available quantity</span>
                  {selectedStock ? <strong>{formatQuantity(available)} units</strong> : <span>Select an item to view stock</span>}
                </div>
                <Field label="Transaction quantity" id="movement-quantity">
                  <input
                    id="movement-quantity"
                    type="number"
                    min="1"
                    max={movementType === "OUT" ? available : undefined}
                    step="1"
                    required
                    value={quantity}
                    onChange={(event) => setQuantity(event.target.value)}
                    aria-describedby={exceedsAvailable ? "quantity-validation" : "quantity-preview"}
                  />
                  {exceedsAvailable
                    ? <small id="quantity-validation" className="field-error">Quantity cannot exceed the available {formatQuantity(available)} units.</small>
                    : <small id="quantity-preview" className="field-hint">Expected quantity after submit: {formatQuantity(Math.max(0, expectedQuantity))} units.</small>}
                </Field>
                <Field label="Remarks (optional)" id="movement-remarks">
                  <textarea id="movement-remarks" rows="3" maxLength="500" value={remarks} onChange={(event) => setRemarks(event.target.value)} placeholder="Add a short note about this movement" />
                </Field>
                <Field label="Recorded by" id="movement-user">
                  <input id="movement-user" maxLength="128" required value={createdBy} onChange={(event) => setCreatedBy(event.target.value)} />
                  <small className="field-hint">Demo attribution only; this app does not authenticate users.</small>
                </Field>
                {message && <Feedback>{message}</Feedback>}
                {errorMessage && <Feedback kind="error">{errorMessage}</Feedback>}
                <button className="button button-primary button-full" disabled={submitting || !itemId || !quantity || exceedsAvailable}>
                  {submitting ? "Submitting..." : movementType === "IN" ? "Record stock in" : "Record stock out"}
                </button>
              </form>
            </Card>

            <Card title="Current stock" subtitle="Live quantities from the API">
              {stock.data.length ? (
                <div className="balance-list">
                  {stock.data.map((row) => {
                    const low = row.quantity_on_hand <= row.reorder_level;
                    return (
                      <button
                        key={row.item_id}
                        className={`balance-row${itemId === String(row.item_id) ? " balance-row-selected" : ""}`}
                        onClick={() => setItemId(String(row.item_id))}
                      >
                        <div className="balance-item-icon"><Boxes size={17} /></div>
                        <div className="balance-item-copy">
                          <strong>{row.item_name}</strong>
                          <span>{row.sku} · reorder at {formatQuantity(row.reorder_level)}</span>
                        </div>
                        <div className="balance-quantity">
                          <strong>{formatQuantity(row.quantity_on_hand)}</strong>
                          {row.quantity_on_hand === 0
                            ? <StatusPill tone="danger">Out</StatusPill>
                            : low ? <StatusPill tone="warning">Low</StatusPill> : <StatusPill tone="success">OK</StatusPill>}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : <EmptyState title="No stock records" description="Create an item to add its initial stock balance." />}
            </Card>
          </div>
        </>
      )}
    </section>
  );
}
