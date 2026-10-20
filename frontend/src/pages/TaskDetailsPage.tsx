import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { deleteTask, getTask, updateTask } from "../api/tasks";
import { ErrorMessage, Loading, PageHeader, PriorityPill, StatusPill } from "../components/Shared";
import type { Task } from "../types";

export function TaskDetailsPage() {
  const { taskId } = useParams();
  const id = Number(taskId);
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      if (!Number.isSafeInteger(id) || id < 1) throw new ApiError("That task address is not valid.", 400);
      setTask(await getTask(id));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load this task.");
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => { void load(); }, [load]);

  async function toggleStatus() {
    if (!task) return;
    try {
      setTask(await updateTask(task.id, {
        status: task.status === "completed" ? "pending" : "completed",
      }));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update this task.");
    }
  }

  async function remove() {
    if (!task || !window.confirm(`Delete “${task.title}”? This cannot be undone.`)) return;
    try {
      await deleteTask(task.id);
      navigate("/tasks", { replace: true });
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not delete this task.");
    }
  }

  return (
    <div className="page-content form-page">
      <PageHeader
        eyebrow="TASK DETAILS"
        title={task?.title ?? "Task"}
        subtitle="Keep the details close, and the next step clear."
        action={task && <Link className="button button-outline" to={`/tasks/${task.id}/edit`}>Edit task</Link>}
      />
      {error && <ErrorMessage message={error} onRetry={() => void load()} />}
      {loading ? <Loading label="Loading task…" /> : task && (
        <article className="panel detail-card">
          <div className="detail-badges">
            <StatusPill status={task.status} />
            <PriorityPill priority={task.priority} />
          </div>
          <h2>{task.title}</h2>
          <p className="detail-description">{task.description || "No description added."}</p>
          <dl className="detail-meta">
            <div><dt>Due date</dt><dd>{task.due_date ? new Date(task.due_date).toLocaleString() : "No due date"}</dd></div>
            <div><dt>Created</dt><dd>{new Date(task.created_at).toLocaleString()}</dd></div>
            <div><dt>Last updated</dt><dd>{new Date(task.updated_at).toLocaleString()}</dd></div>
            {task.completed_at && <div><dt>Completed</dt><dd>{new Date(task.completed_at).toLocaleString()}</dd></div>}
          </dl>
          <div className="form-actions">
            <Link className="button button-outline" to="/tasks">Back to tasks</Link>
            <button className="button button-secondary" onClick={() => void toggleStatus()}>
              {task.status === "completed" ? "Reopen task" : "Mark complete"}
            </button>
            <button className="button button-danger" onClick={() => void remove()}>Delete</button>
          </div>
        </article>
      )}
    </div>
  );
}
