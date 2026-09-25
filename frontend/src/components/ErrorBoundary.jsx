import React from "react";
import { FiAlertCircle, FiRefreshCw, FiHome } from "react-icons/fi";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Fresher.AI Runtime Error Caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#F8F9FB] flex flex-col items-center justify-center p-6 text-slate-800">
          <div className="max-w-md w-full p-8 rounded-3xl bg-white border border-rose-100 shadow-[0_8px_32px_rgba(225,29,72,0.08)] text-center">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-rose-50 border border-rose-100 text-rose-500 flex items-center justify-center mb-4">
              <FiAlertCircle size={28} />
            </div>

            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Something went wrong
            </h2>

            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              We encountered an unexpected issue while rendering this page. You can reload the page or return to the homepage safely.
            </p>

            <div className="mt-6 flex items-center justify-center gap-3">
              <button
                onClick={this.handleReload}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition-all"
              >
                <FiRefreshCw size={14} />
                <span>Reload Page</span>
              </button>

              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-all"
              >
                <FiHome size={14} />
                <span>Return Home</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
