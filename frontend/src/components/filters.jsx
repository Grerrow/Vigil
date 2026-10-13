
import { useState } from "react";

function Filters({ onApplyFilters }) {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState("");

  function handleApplyFilters() {
    onApplyFilters({ startDate, endDate, confidenceThreshold });
  }

  function handleClearFilters() {
    setStartDate("");
    setEndDate("");
    setConfidenceThreshold("");
    onApplyFilters({});
  }

  return (
    <div className="filters card">
      <label>
        From
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
      </label>
      <label>
        To
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      </label>
      <label>
        Min confidence (0–1)
        <input type="number" min="0" max="1" step="0.05" value={confidenceThreshold} onChange={(e) => setConfidenceThreshold(e.target.value)} />
      </label>
      <div className="filters-actions">
        <button className="btn btn-primary" onClick={handleApplyFilters}>Apply</button>
        <button className="btn" onClick={handleClearFilters}>Clear</button>
      </div>
    </div>
  );
}

export default Filters;