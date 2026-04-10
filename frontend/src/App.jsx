import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value || 0);
}

async function parseResponse(response) {
  if (!response.ok) {
    const fallback = `Request failed (${response.status})`;
    try {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || fallback);
    } catch {
      throw new Error(fallback);
    }
  }
  return response.json();
}

export default function App() {
  const [customers, setCustomers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [prediction, setPrediction] = useState(null);

  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("");

  const [loadingCustomers, setLoadingCustomers] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchDraft.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchDraft]);

  useEffect(() => {
    async function loadCountries() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/countries`);
        const payload = await parseResponse(response);
        setCountries(payload.countries || []);
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    loadCountries();
  }, []);

  useEffect(() => {
    async function loadCustomers() {
      setLoadingCustomers(true);
      setError("");
      setPrediction(null);

      try {
        const query = new URLSearchParams({ limit: "60" });
        if (search) {
          query.set("search", search);
        }
        if (country) {
          query.set("country", country);
        }

        const response = await fetch(`${API_BASE_URL}/api/customers?${query.toString()}`);
        const payload = await parseResponse(response);
        setCustomers(payload.customers || []);

        const firstCustomer = payload.customers?.[0]?.customer_id || null;
        setSelectedCustomerId((currentId) => {
          if (currentId && payload.customers?.some((entry) => entry.customer_id === currentId)) {
            return currentId;
          }
          return firstCustomer;
        });
      } catch (loadError) {
        setCustomers([]);
        setSelectedCustomerId(null);
        setError(loadError.message);
      } finally {
        setLoadingCustomers(false);
      }
    }

    loadCustomers();
  }, [country, search]);

  useEffect(() => {
    async function loadCustomerDetail() {
      if (!selectedCustomerId) {
        setSelectedDetail(null);
        return;
      }

      setLoadingDetail(true);
      setError("");

      try {
        const response = await fetch(`${API_BASE_URL}/api/customers/${selectedCustomerId}`);
        const payload = await parseResponse(response);
        setSelectedDetail(payload);
      } catch (loadError) {
        setSelectedDetail(null);
        setError(loadError.message);
      } finally {
        setLoadingDetail(false);
      }
    }

    loadCustomerDetail();
  }, [selectedCustomerId]);

  const totalRevenueShown = useMemo(() => {
    const total = customers.reduce((sum, customer) => sum + (customer.monetary || 0), 0);
    return formatCurrency(total);
  }, [customers]);

  const averageRecency = useMemo(() => {
    if (!customers.length) {
      return 0;
    }
    return Math.round(customers.reduce((sum, customer) => sum + customer.recency_days, 0) / customers.length);
  }, [customers]);

  async function runPrediction() {
    if (!selectedCustomerId) {
      return;
    }
    setLoadingPrediction(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${selectedCustomerId}/prediction`, {
        method: "POST",
      });
      const payload = await parseResponse(response);
      setPrediction(payload);
    } catch (predictionError) {
      setPrediction(null);
      setError(predictionError.message);
    } finally {
      setLoadingPrediction(false);
    }
  }

  return (
    <div className="crm-shell">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />

      <header className="crm-header">
        <div>
          <p className="eyebrow">Customer Relationship Management</p>
          <h1>Retail Intelligence Console</h1>
          <p className="subtitle">FastAPI + MLFlow + React dashboard with customer-value prediction.</p>
        </div>
      </header>

      <section className="kpi-row">
        <article className="kpi-card">
          <span>Visible Customers</span>
          <strong>{customers.length}</strong>
        </article>
        <article className="kpi-card">
          <span>Revenue (Visible)</span>
          <strong>{totalRevenueShown}</strong>
        </article>
        <article className="kpi-card">
          <span>Average Recency</span>
          <strong>{averageRecency} days</strong>
        </article>
      </section>

      <section className="controls">
        <label>
          Search Customer / Country
          <input
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            placeholder="e.g. 13085 or United Kingdom"
          />
        </label>
        <label>
          Country
          <select value={country} onChange={(event) => setCountry(event.target.value)}>
            <option value="">All Countries</option>
            {countries.map((countryName) => (
              <option value={countryName} key={countryName}>
                {countryName}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <main className="crm-grid">
        <section className="customer-list-panel">
          <h2>Customers</h2>
          {loadingCustomers ? <p className="loading">Loading customer list...</p> : null}
          {!loadingCustomers && customers.length === 0 ? <p className="loading">No customers matched your filters.</p> : null}
          <div className="customer-list">
            {customers.map((customer) => (
              <button
                type="button"
                key={customer.customer_id}
                className={customer.customer_id === selectedCustomerId ? "customer-card active" : "customer-card"}
                onClick={() => {
                  setSelectedCustomerId(customer.customer_id);
                  setPrediction(null);
                }}
              >
                <div>
                  <h3>#{customer.customer_id}</h3>
                  <p>{customer.country}</p>
                </div>
                <div className="card-metrics">
                  <span>{formatCurrency(customer.monetary)}</span>
                  <small>{customer.frequency} invoices</small>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="detail-panel">
          <h2>Customer Insights</h2>
          {loadingDetail ? <p className="loading">Loading details...</p> : null}

          {selectedDetail ? (
            <>
              <div className="detail-grid">
                <div>
                  <span>Customer</span>
                  <strong>#{selectedDetail.customer_id}</strong>
                </div>
                <div>
                  <span>Country</span>
                  <strong>{selectedDetail.country}</strong>
                </div>
                <div>
                  <span>First Purchase</span>
                  <strong>{selectedDetail.first_purchase_date}</strong>
                </div>
                <div>
                  <span>Last Purchase</span>
                  <strong>{selectedDetail.last_purchase_date}</strong>
                </div>
                <div>
                  <span>Total Monetary</span>
                  <strong>{formatCurrency(selectedDetail.monetary)}</strong>
                </div>
                <div>
                  <span>Avg Line Amount</span>
                  <strong>{formatCurrency(selectedDetail.average_line_amount)}</strong>
                </div>
                <div>
                  <span>Quantity Sold</span>
                  <strong>{selectedDetail.quantity_sum}</strong>
                </div>
                <div>
                  <span>Purchase Rate</span>
                  <strong>{selectedDetail.purchase_rate}</strong>
                </div>
              </div>

              <button type="button" className="predict-btn" onClick={runPrediction} disabled={loadingPrediction}>
                {loadingPrediction ? "Scoring..." : "Predict Customer Value"}
              </button>

              {prediction ? (
                <div className="prediction-card">
                  <p>
                    Segment: <strong>{prediction.segment}</strong>
                  </p>
                  <p>
                    Probability High Value: <strong>{(prediction.probability_high_value * 100).toFixed(2)}%</strong>
                  </p>
                  <p>Model Source: {prediction.model_source}</p>
                </div>
              ) : null}
            </>
          ) : (
            <p className="loading">Select a customer to view details.</p>
          )}
        </section>
      </main>
    </div>
  );
}
