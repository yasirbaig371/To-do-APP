import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Task, TaskPriority, TaskStatus } from "../types";

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {action && <div className="page-header-action">{action}</div>}
    </div>
  );
}

export function Loading({ label = "Loading your workspace…" }: { label?: string }) {
  return (
    <div className="loading-state" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorMessage({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="alert alert-error" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button className="text-button" type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function StatusPill({ status }: { status: TaskStatus }) {
  const labels: Record<TaskStatus, string> = {
    pending: "To do",
    in_progress: "In progress",
    completed: "Done",
  };
  return <span className={`status-pill status-${status}`}>{labels[status]}</span>;
}

export function PriorityPill({ priority }: { priority: TaskPriority }) {
  return (
    <span className={`priority priority-${priority}`}>
      <span aria-hidden="true">●</span> {priority}
    </span>
  );
}

export function TaskList({
  tasks,
  onToggle,
  onDelete,
}: {
  tasks: Task[];
  onToggle?: (task: Task) => void;
  onDelete?: (task: Task) => void;
}) {
  if (tasks.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-icon" aria-hidden="true">✳</span>
        <h3>Nothing on your list</h3>
        <p>A little progress adds up. Create a task to get started.</p>
        <Link className="button button-primary button-small" to="/tasks/new">
          Create your first task
        </Link>
      </div>
    );
  }
  return (
    <div className="task-list">
      {tasks.map((task) => (
        <article className="task-row" key={task.id}>
          {onToggle && (
            <button
              className={`task-check ${task.status === "completed" ? "task-check-done" : ""}`}
              type="button"
              aria-label={task.status === "completed" ? "Reopen task" : "Complete task"}
              title={task.status === "completed" ? "Reopen task" : "Mark complete"}
              onClick={() => onToggle(task)}
            >
              {task.status === "completed" ? "✓" : ""}
            </button>
          )}
          <Link className="task-main" to={`/tasks/${task.id}`}>
            <strong className={task.status === "completed" ? "task-title-done" : ""}>
              {task.title}
            </strong>
            <span className="task-meta">
              <StatusPill status={task.status} />
              <PriorityPill priority={task.priority} />
              {task.due_date && (
                <span className="task-due">
                  Due {new Date(task.due_date).toLocaleDateString()}
                </span>
              )}
            </span>
          </Link>
          <div className="task-actions">
            <Link className="icon-button" to={`/tasks/${task.id}/edit`} aria-label={`Edit ${task.title}`}>
              ↗
            </Link>
            {onDelete && (
              <button
                className="icon-button icon-button-danger"
                type="button"
                aria-label={`Delete ${task.title}`}
                onClick={() => onDelete(task)}
              >
                ×
              </button>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

export function StatCard({
  label,
  value,
  accent,
  note,
}: {
  label: string;
  value: number | string;
  accent: string;
  note?: string;
}) {
  return (
    <article className="stat-card">
      <span className={`stat-dot ${accent}`} aria-hidden="true" />
      <p>{label}</p>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </article>
  );
}
