// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import SignUp from "./pages/SignUp";
import SignIn from "./pages/SignIn";
import Loading from "./pages/Loading";
import Simulator from "./pages/Simulator";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SignUp />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/loading" element={<Loading />} />
        <Route path="/simulate" element={<Simulator />} />
      </Routes>
    </Router>
  );
}
