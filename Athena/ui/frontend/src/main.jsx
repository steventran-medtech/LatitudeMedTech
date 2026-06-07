import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { initTabGuard } from "./tabGuard.js";

if (initTabGuard()) {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
