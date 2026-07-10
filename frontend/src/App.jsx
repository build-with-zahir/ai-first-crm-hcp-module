import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AlertTriangle, DatabaseZap, RefreshCw } from "lucide-react";

import ChatCapture from "./components/ChatCapture.jsx";
import InteractionForm from "./components/InteractionForm.jsx";
import Timeline from "./components/Timeline.jsx";
import ToolPanel from "./components/ToolPanel.jsx";
import {
  clearError,
  fetchHcps,
  fetchInteractions,
  seedDemoData,
} from "./features/crmSlice.js";

export default function App() {
  const dispatch = useDispatch();
  const { selectedHcpId, error, loading } = useSelector((state) => state.crm);

  useEffect(() => {
    dispatch(seedDemoData()).then(() => dispatch(fetchHcps()));
  }, [dispatch]);

  useEffect(() => {
    if (selectedHcpId) {
      dispatch(fetchInteractions(selectedHcpId));
    }
  }, [dispatch, selectedHcpId]);

  return (
    <div className="app-shell">
      <main className="video-workspace" aria-busy={loading}>
        <div className="assignment-bar">
          <span>AI-First CRM HCP Module</span>
          <button
            className="demo-button"
            type="button"
            onClick={() => dispatch(seedDemoData()).then(() => dispatch(fetchHcps()))}
            disabled={loading}
            title="Refresh demo data"
          >
            {loading ? <RefreshCw className="spin" size={15} /> : <DatabaseZap size={15} />}
            Demo data
          </button>
        </div>

        {error ? (
          <button className="error-banner" type="button" onClick={() => dispatch(clearError())}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </button>
        ) : null}

        <section className="log-screen">
          <InteractionForm />
          <ChatCapture />
        </section>

        <section className="demo-panels">
          <ToolPanel />
          <Timeline />
        </section>
      </main>
    </div>
  );
}
