import { useEffect, useRef, useState, type FormEvent } from "react";
import { sendChatMessage } from "../api/chat";
import { useAuth } from "../auth/AuthContext";
import { ErrorMessage, Loading, PageHeader } from "../components/Shared";
import type { ChatMessage, ChatResponse } from "../types";

const suggestions = [
  "Show my pending tasks.",
  "Create a task called Prepare project presentation with high priority.",
  "What tasks are overdue?",
];

export function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: `Hi ${user?.full_name ?? "there"}! Ask me to list your work, create a task, or check your task counts.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pendingConfirmation, setPendingConfirmation] = useState<{
    userInput: string;
    response: string;
  } | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, pendingConfirmation]);

  async function submitChat(inputText: string, confirm = false) {
    const trimmed = inputText.trim();
    if (!trimmed || loading) return;

    const nextUserMessage: ChatMessage = { role: "user", content: trimmed };
    const history = [...messages, nextUserMessage];
    setInput("");
    setError("");
    setLoading(true);
    setPendingConfirmation(null);

    try {
      const response: ChatResponse = await sendChatMessage(trimmed, history, confirm);
      setMessages((current) => [...current, nextUserMessage, { role: "assistant", content: response.response }]);

      if (response.requires_confirmation) {
        setPendingConfirmation({
          userInput: trimmed,
          response: response.response,
        });
      }
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "The assistant could not complete that request.";
      setError(message);
      setMessages((current) => [...current, nextUserMessage]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitChat(input, false);
  }

  function handleConfirm() {
    if (!pendingConfirmation) return;
    void submitChat(pendingConfirmation.userInput, true);
  }

  return (
    <div className="page-content chat-page">
      <PageHeader
        eyebrow="AI ASSISTANT"
        title="Chat assistant"
        subtitle="Ask for task updates, summaries, or account actions using natural language."
      />

      {error && <ErrorMessage message={error} onRetry={() => setError("")} />}

      <section className="chat-shell" aria-live="polite">
        <div className="chat-header">
          <div className="profile-mini">
            <span className="avatar" aria-hidden="true">✦</span>
            <span className="profile-mini-copy">
              <strong>Assistant</strong>
              <small>Online</small>
            </span>
          </div>
        </div>

        <div className="chat-messages" role="log" aria-label="Assistant conversation">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`chat-bubble chat-bubble-${message.role}`}>
              {message.content}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble chat-bubble-assistant">
              <Loading label="Assistant is thinking…" />
            </div>
          )}
          <div ref={endRef} />
        </div>

        {pendingConfirmation && (
          <div className="chat-confirmation" role="alert">
            <p>{pendingConfirmation.response}</p>
            <div className="chat-confirmation-actions">
              <button type="button" className="button button-danger button-small" onClick={handleConfirm}>
                Confirm action
              </button>
              <button type="button" className="button button-outline button-small" onClick={() => setPendingConfirmation(null)}>
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="chat-suggestions" aria-label="Suggested prompts">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="chat-suggestion"
              onClick={() => setInput(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>

        <form className="chat-form" onSubmit={handleSubmit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submitChat(input, false);
              }
            }}
            rows={1}
            placeholder="Message the assistant…"
            aria-label="Message assistant"
          />
          <button type="submit" className="button button-primary" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </section>
    </div>
  );
}
