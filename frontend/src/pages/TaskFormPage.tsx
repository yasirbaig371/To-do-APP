import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { createTask, getTask, updateTask, type TaskInput } from "../api/tasks";
import { ErrorMessage, Loading, PageHeader } from "../components/Shared";
import type { TaskPriority, TaskStatus } from "../types";

export function TaskFormPage({ editing = false }: { editing?: boolean }) {
  const { taskId } = useParams();
  const id = Number(taskId);
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>("pending");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [dueDate, setDueDate] = useState("");
  const [loading, setLoading] = useState(editing);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!editing) return;
    if (!Number.isSafeInteger(id) || id < 1) {
      setError("That task address is not valid.");
      setLoading(false);
      return;
    }
    let active = true;
    getTask(id)
      .then((task) => {
        if (!active) return;
        setTitle(task.title);
        setDescription(task.description ?? "");
        setStatus(task.status);
        setPriority(task.priority);
        setDueDate(task.due_date ? toLocalDateTime(task.due_date) : "");
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof ApiError ? cause.message : "Could not load this task.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [editing, id]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const payload: TaskInput = {
      title: title.trim(),
      description: description.trim() || null,
      status,
      priority,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
    };
    try {
      const task = editing
        ? await updateTask(id, payload)
        : await createTask(payload);
      navigate(`/tasks/${task.id}`, { replace: true });
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not save this task.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="page-content"><Loading label="Loading task…" /></div>;

  return (
    <div className="page-content form-page">
      <PageHeader
        eyebrow="YOUR WORKSPACE"
        title={editing ? "Shape the details" : "Make it happen"}
        subtitle={editing ? "Update your task details." : "Add one clear next step to your list."}
      />
      {error && <ErrorMessage message={error} />}
      <form className="panel form-stack task-form" onSubmit={submit}>
        <label className="field">
          <span>Task title <small>Required</small></span>
          <input
            autoFocus
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={200}
            placeholder="What needs to get done?"
            required
          />
        </label>
        <label className="field">
          <span>Description <small>Optional</small></span>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={10000}
            rows={5}
            placeholder="Add a little context or break it into steps…"
          />
        </label>
        <div className="form-grid">
          <label className="field">
            <span>Priority</span>
            <select value={priority} onChange={(event) => setPriority(event.target.value as TaskPriority)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          {editing && (
            <label className="field">
              <span>Status</span>
              <select value={status} onChange={(event) => setStatus(event.target.value as TaskStatus)}>
                <option value="pending">To do</option>
                <option value="in_progress">In progress</option>
                <option value="completed">Done</option>
              </select>
            </label>
          )}
          <label className="field">
            <span>Due date <small>Optional</small></span>
            <input
              type="datetime-local"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
          </label>
        </div>
        <div className="form-actions">
          <Link className="button button-outline" to={editing ? `/tasks/${id}` : "/tasks"}>Cancel</Link>
          <button className="button button-primary" disabled={busy || !title.trim()}>
            {busy ? "Saving…" : editing ? "Save changes" : "Create task"}
          </button>
        </div>
      </form>
    </div>
  );
}

function toLocalDateTime(value: string): string {
  const date = new Date(value);
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return offsetDate.toISOString().slice(0, 16);
}
