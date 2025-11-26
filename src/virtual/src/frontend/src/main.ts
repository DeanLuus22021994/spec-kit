import React from "react";
import ReactDOM from "react-dom";
import "semantic-ui-css/semantic.min.css";
import App from "./App";
import { ErrorBoundary } from "./components";
import "./styles/components.css";

/**
 * Main application entry point
 * Wraps the App component in an ErrorBoundary for graceful error handling
 */
const AppWithErrorBoundary = React.createElement(ErrorBoundary, {
  children: React.createElement(App),
  onError: (error: Error, errorInfo: React.ErrorInfo): void => {
    // Log to console in development
    console.error("Application error:", error.message);
    console.error("Component stack:", errorInfo.componentStack);

    // In production, you could send this to an error tracking service
    // Example: sendToErrorTrackingService(error, errorInfo);
  },
});

const rootElement = document.getElementById("root");
if (rootElement) {
  ReactDOM.render(AppWithErrorBoundary, rootElement);
} else {
  console.error("Failed to find root element");
}
