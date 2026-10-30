import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, DataTable, EmptyState, ErrorState, formatDate, formatQuantity, LoadingState, PageTitle, StatusPill } from "../components/Ui.jsx";
import { useApi } from "../hooks/useApi.js";

function MetricCard({ label, value, accent, note }) {
  return (
    <article className="card metric-card">
      <span className={`metric-accent metric-accent-${accent}`} />
      <p>{label}</p>
      <strong>{formatQuantity(value)}</strong>
      <span className="metric-note">{note}</span>
    </article>
  );
}

function ChartPlaceholder({ rows, title }) {
  if (rows?.length) return false;
  return <EmptyState title="No chart data yet" description={`${title} will appear when the API has matching records.`} />;
}

export default function OverviewPage() {
  const [periodDays, setPeriodDays] = useState(30);
  const { data, loading, error, reload } = useApi("/dashboard/summary", { period_days: periodDays });

  const recentColumns = [
    { key: "item_name", label: "Item" },
    {
      key: "transaction_type",
      label: "Type",
      render: (row) => <StatusPill tone={row.transaction_type === "IN" ? "success" : "info"}>{row.transaction_type}</StatusPill>,
    },
    { key: "quantity", label: "Quantity", render: (row) => formatQuantity(row.quantity) },
    { key: "transaction_date", label: "Date", render: (row) => formatDate(row.transaction_date, true) },
  ];

  const updatePeriod = (event) => setPeriodDays(Number(event.target.value));

  return (
    <section className="page-section">
      <PageTitle
        title="Overview"
        description="A live snapshot of stock levels and inventory activity."
        action={
          <label className="period-control">
            <span>Activity period</span>
            <select value={periodDays} onChange={updatePeriod} aria-label="Dashboard activity period">
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </label>
        }
      />

      {loading && !data && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="metrics-grid">
            <MetricCard label="Unique items" value={data.total_unique_items} accent="blue" note="Catalog item count" />
            <MetricCard label="Units in stock" value={data.total_units_in_stock} accent="green" note="Current on-hand quantity" />
            <MetricCard label="Low-stock items" value={data.low_stock_items} accent="orange" note="At or below reorder level" />
            <MetricCard label="Out of stock" value={data.out_of_stock_items} accent="red" note="Current quantity is zero" />
            <MetricCard label={`Units received · ${periodDays}d`} value={data.stock_received_in_period} accent="blue" note="IN transaction quantity" />
            <MetricCard label={`Units issued · ${periodDays}d`} value={data.stock_issued_in_period} accent="violet" note="OUT transaction quantity" />
          </div>

          <div className="dashboard-charts">
            <Card title="Stock quantity by category" subtitle="Current units on hand">
              <div className="chart-area">
                {data.stock_by_category.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.stock_by_category} margin={{ top: 12, right: 10, left: -15, bottom: 4 }}>
                      <CartesianGrid stroke="#edf0f5" vertical={false} />
                      <XAxis dataKey="category" tickLine={false} axisLine={false} tick={{ fill: "#778399", fontSize: 11 }} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#778399", fontSize: 10 }} />
                      <Tooltip formatter={(value) => formatQuantity(value)} />
                      <Bar dataKey="quantity_on_hand" name="Units" fill="#4e7fe7" radius={[5, 5, 0, 0]} maxBarSize={44} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <ChartPlaceholder rows={data.stock_by_category} title="Category totals" />}
              </div>
            </Card>

            <Card title="Stock in vs. out" subtitle={`Daily units during the last ${periodDays} days`}>
              <div className="chart-area">
                {data.movement_by_day.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.movement_by_day} margin={{ top: 12, right: 14, left: -15, bottom: 4 }}>
                      <CartesianGrid stroke="#edf0f5" vertical={false} />
                      <XAxis
                        dataKey="transaction_day"
                        tickLine={false}
                        axisLine={false}
                        tick={{ fill: "#778399", fontSize: 10 }}
                        tickFormatter={(value) => new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                      />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#778399", fontSize: 10 }} />
                      <Tooltip labelFormatter={(value) => formatDate(value)} formatter={(value) => formatQuantity(value)} />
                      <Legend />
                      <Line type="monotone" dataKey="stock_in" name="Stock in" stroke="#17875e" strokeWidth={2.5} dot={{ r: 3 }} />
                      <Line type="monotone" dataKey="stock_out" name="Stock out" stroke="#e08239" strokeWidth={2.5} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <ChartPlaceholder rows={data.movement_by_day} title="Stock movement" />}
              </div>
            </Card>

            <Card title="Low-stock comparison" subtitle="On-hand quantity compared with reorder level">
              <div className="chart-area chart-area-tall">
                {data.low_stock_comparison.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={data.low_stock_comparison.slice(0, 8)}
                      layout="vertical"
                      margin={{ top: 4, right: 16, left: 4, bottom: 4 }}
                    >
                      <CartesianGrid stroke="#edf0f5" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#778399", fontSize: 10 }} />
                      <YAxis type="category" dataKey="item_name" width={92} tickLine={false} axisLine={false} tick={{ fill: "#657188", fontSize: 10 }} />
                      <Tooltip formatter={(value) => formatQuantity(value)} />
                      <Legend />
                      <Bar dataKey="quantity_on_hand" name="On hand" fill="#e08b35" radius={[0, 4, 4, 0]} />
                      <Bar dataKey="reorder_level" name="Reorder level" fill="#dce3ef" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <ChartPlaceholder rows={data.low_stock_comparison} title="Low-stock comparison" />}
              </div>
            </Card>

            <Card title="Recent transaction activity" subtitle="Latest stock movements">
              {data.recent_transactions.length ? (
                <DataTable columns={recentColumns} rows={data.recent_transactions} rowKey={(row) => row.transaction_id} minWidth={440} />
              ) : <EmptyState title="No stock activity yet" description="Receipts and issues will appear here after they are recorded." />}
            </Card>
          </div>
        </>
      )}
    </section>
  );
}
