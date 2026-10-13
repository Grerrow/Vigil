import { useEffect, useState } from "react";
import axios from "axios";
import Filters from "../components/filters.jsx";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function HistoryView() {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  function fetchHistory(filters = {}) {
    setIsLoading(true);
    setError(null);
    axios
      .get(`${API_BASE_URL}/history`, {
        params: {
          start: filters.startDate || undefined,
          end: filters.endDate ? `${filters.endDate}T23:59:59` : undefined,
          min_confidence: filters.confidenceThreshold || undefined,
        },
      })
      .then((response) => setHistory(response.data.history))
      .catch((err) => setError(err.response?.data?.detail ?? err.message))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    let active = true;
    axios
      .get(`${API_BASE_URL}/history`)
      .then((response) => {
        if (active) {
          setHistory(response.data.history);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.response?.data?.detail ?? err.message);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  function handleReset() {
    setIsLoading(true);
    setError(null);
    axios
      .post(`${API_BASE_URL}/reset`)
      .then(() => setHistory([]))
      .catch((err) => setError(err.response?.data?.detail ?? err.message))
      .finally(() => setIsLoading(false));
  }

  return (
    <section>
      <div className="page-header">
        <h2>Detection history</h2>
        <p>Every detection is stored with its count, confidence and inference time.</p>
      </div>

      <Filters onApplyFilters={fetchHistory} />

      {isLoading && <p className="empty">Loading…</p>}
      {error && <div className="error">{error}</div>}
      {!isLoading && !error && history.length === 0 && (
        <p className="empty">No detections found. Run a detection, or adjust the filters.</p>
      )}

      {history.length > 1 && (
        <div className="card chart">
          <h3>People per detection</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={[...history].reverse()}>
              <CartesianGrid stroke="#243047" strokeDasharray="3 3" />
              <XAxis dataKey="id" stroke="#9aa7bd" />
              <YAxis allowDecimals={false} stroke="#9aa7bd" />
              <Tooltip
                contentStyle={{ background: "#131a26", border: "1px solid #243047" }}
                labelFormatter={(id) => `Detection #${id}`}
              />
              <Line type="monotone" dataKey="person_count" name="People" stroke="#34d399" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {history.length > 0 && (
        <>
          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Timestamp</th>
                  <th>People</th>
                  <th>Avg confidence</th>
                  <th>Inference</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{new Date(item.timestamp).toLocaleString()}</td>
                    <td>{item.person_count}</td>
                    <td>{(item.average_confidence * 100).toFixed(1)}%</td>
                    <td>{item.inference_time_ms.toFixed(0)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footer">
            <span>{history.length} record{history.length === 1 ? "" : "s"}</span>
            <button className="btn btn-danger" onClick={handleReset} disabled={isLoading}>
              Reset history
            </button>
          </div>
        </>
      )}
    </section>
  );
}

export default HistoryView;
