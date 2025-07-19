// src/pages/SignUp.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SignUp() {
  const [form, setForm] = useState({ username: "", password: "", ticker: "" });
  const navigate = useNavigate();

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch("http://localhost:5000/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (res.ok) navigate("/signin");
    else alert(data.error || "Signup failed");
  };

  return (
    <div className="page">
      <h2>Sign Up</h2>
      <form onSubmit={handleSubmit}>
        <input name="username" placeholder="Username" onChange={handleChange} required />
        <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
        <input name="ticker" placeholder="Ticker Symbol" onChange={handleChange} required />
        <button type="submit">Register</button>
      </form>
    </div>
  );
}
