// src/pages/Loading.jsx
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Loading() {
  const navigate = useNavigate();

  useEffect(() => {
    const ticker = localStorage.getItem("ticker");
    if (!ticker) return navigate("/signin");

    fetch("http://localhost:5000/process_ticker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.risks) {
          localStorage.setItem("risks", JSON.stringify(data.risks));
          navigate("/simulate");
        } else {
          alert("Processing failed");
        }
      })
      .catch(() => alert("Failed to process ticker"));
  }, [navigate]);

  return <div className="page">Processing your ticker... please wait ⏳</div>;
}
