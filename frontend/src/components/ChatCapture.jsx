import { Bot, Loader2, SendHorizonal, Sparkles, UserRound } from "lucide-react";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { addUserChatMessage, chatAgent } from "../features/crmSlice.js";

const demoPrompt =
  "Met Dr. Smith, discussed CardioFlow efficacy, positive sentiment, shared brochure, and asked for follow-up next week.";

export default function ChatCapture() {
  const dispatch = useDispatch();
  const { chatMessages, saving, selectedHcpId } = useSelector((state) => state.crm);
  const [message, setMessage] = useState(demoPrompt);

  function submitMessage(event) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }
    dispatch(addUserChatMessage(trimmed));
    dispatch(chatAgent(trimmed));
    setMessage("");
  }

  return (
    <section className="chat-panel">
      <div className="assistant-heading">
        <Sparkles size={17} />
        <div>
          <h2>AI Assistant</h2>
          <p>Log interaction details here via chat</p>
        </div>
      </div>

      <div className="chat-transcript">
        <div className="assistant-hint">
          Log interaction details here (e.g., "Met Dr. Smith, discussed CardioFlow efficacy,
          positive sentiment, shared brochure") or ask for help.
        </div>
        {chatMessages.map((chat, index) => (
          <div className={`chat-row ${chat.role}`} key={`${chat.role}-${index}`}>
            <span className="chat-icon">
              {chat.role === "assistant" ? <Bot size={16} /> : <UserRound size={16} />}
            </span>
            <p>{chat.content}</p>
          </div>
        ))}
        {saving ? (
          <div className="chat-row assistant">
            <span className="chat-icon">
              <Loader2 className="spin" size={16} />
            </span>
            <p>Agent is selecting tools...</p>
          </div>
        ) : null}
      </div>

      <form className="chat-input" onSubmit={submitMessage}>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          disabled={!selectedHcpId}
          rows={3}
          placeholder="Describe Interaction..."
        />
        <button
          className="icon-button"
          type="submit"
          disabled={!selectedHcpId || saving}
          title="AI Log"
        >
          <SendHorizonal size={18} />
          <span>AI Log</span>
        </button>
      </form>
    </section>
  );
}
