import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import { deleteTask, listTasks, updateTask } from "../api/tasks";
import {
  ErrorMessage,
  Loading,
  PageHeader,
  TaskList,
} from "../components/Shared";
import type { Task, TaskPriority, TaskStatus } from "../types";

const PAGE_SIZE = 20;

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [priority, setPriority] = useState<TaskPriority | "">("");
  const [sortBy, setSortBy] = useState<"created_at" | "due_date" | "title">("created_at");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await listTasks({
        status,
        priority,
        search,
        sort_by: sortBy,
        sort_order: "desc",
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,
      });
      setTasks(result.slice(0, PAGE_SIZE));
      setHasMore(result.length > PAGE_SIZE);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load tasks.");
    } finally {
      setLoading(false);
    }
  }, [status, priority, search, sortBy, page]);

  useEffect(() => { void load(); }, [load]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(0);
    setSearch(searchInput.trim());
  }

  async function toggleTask(task: Task) {
    setError("");
    setNotice("");
    try {
      await updateTask(task.id, {
        status: task.status === "completed" ? "pending" : "completed",
      });
      setNotice(task.status === "completed" ? "Task reopened." : "Task completed.");
      await load();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update this task.");
    }
  }

  async function removeTask(task: Task) {
    if (!window.confirm(`Delete “${task.title}”? This cannot be undone.`)) return;
    setError("");
    setNotice("");
    try {
      await deleteTask(task.id);
      setNotice("Task deleted.");
      await load();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not delete this task.");
    }
  }

  function changeFilter(update: () => void) {
    update();
    setPage(0);
  }

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="YOUR WORKSPACE"
        title="My tasks"
        subtitle="Make a plan. Find your focus. Keep moving."
        action={<Link className="button button-primary" to="/tasks/new">＋ New task</Link>}
      />
      <section className="filter-panel" aria-label="Task search and filters">
        <form className="search-form" onSubmit={submitSearch}>
          <label className="sr-only" htmlFor="task-search">Search tasks</label>
          <span aria-hidden="true">⌕</span>
          <input
            id="task-search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            maxLength={200}
            placeholder="Search your tasks"
          />
          <button className="button button-secondary button-small">Search</button>
        </form>
        <label className="filter-control">
          <span>Status</span>
          <select value={status} onChange={(event) => changeFilter(() => setStatus(event.target.value as TaskStatus | ""))}>
            <option value="">All statuses</option>
            <option value="pending">To do</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Done</option>
          </select>
        </label>
        <label className="filter-control">
          <span>Priority</span>
          <select value={priority} onChange={(event) => changeFilter(() => setPriority(event.target.value as TaskPriority | ""))}>
            <option value="">All priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="filter-control">
          <span>Sort by</span>
          <select value={sortBy} onChange={(event) => changeFilter(() => setSortBy(event.target.value as typeof sortBy))}>
            <option value="created_at">Recently added</option>
            <option value="due_date">Due date</option>
            <option value="title">Title</option>
          </select>
        </label>
      </section>
      {notice && <p className="alert alert-success" role="status">{notice}</p>}
      {error && <ErrorMessage message={error} onRetry={() => void load()} />}
      <section className="content-section task-results">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{search ? `RESULTS FOR “${search}”` : "YOUR LIST"}</p>
            <h2>{status ? status.replace("_", " ") : "All tasks"}</h2>
          </div>
          <span className="result-count">
            {loading ? "Loading…" : `${tasks.length}${hasMore ? "+" : ""} shown`}
          </span>
        </div>
        {loading ? (
          <Loading label="Loading tasks…" />
        ) : (
          <TaskList tasks={tasks} onToggle={(task) => void toggleTask(task)} onDelete={(task) => void removeTask(task)} />
        )}
      </section>
      <div className="pagination">
        <button
          className="button button-outline button-small"
          disabled={page === 0 || loading}
          onClick={() => setPage((value) => Math.max(0, value - 1))}
        >
          ← Previous
        </button>
        <span>Page {page + 1}</span>
        <button
          className="button button-outline button-small"
          disabled={!hasMore || loading}
          onClick={() => setPage((value) => value + 1)}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
