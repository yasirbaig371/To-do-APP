import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyStatistics } from "../api/users";
import { listTasks } from "../api/tasks";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorMessage, Loading, PageHeader, StatCard, TaskList } from "../components/Shared";
import type { Task, UserTaskStatistics } from "../types";

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<UserTaskStatistics | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [statistics, taskList] = await Promise.all([
        getMyStatistics(),
        listTasks({ limit: 5, sort_by: "created_at", sort_order: "desc" }),
      ]);
      setStats(statistics);
      setTasks(taskList);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load your dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="YOUR WORKSPACE"
        title={`Good ${greeting()}, ${user?.full_name.split(" ")[0] ?? "there"}.`}
        subtitle="A little focus goes a long way. Here's where things stand."
        action={<Link className="button button-primary" to="/tasks/new">＋ New task</Link>}
      />
      {error && <ErrorMessage message={error} onRetry={() => void load()} />}
      {loading ? <Loading /> : stats && (
        <>
          <section className="stats-grid" aria-label="Your task statistics">
            <StatCard label="All tasks" value={stats.total} accent="accent-ink" />
            <StatCard label="To do" value={stats.pending} accent="accent-amber" />
            <StatCard label="In progress" value={stats.in_progress} accent="accent-blue" />
            <StatCard label="Completed" value={stats.completed} accent="accent-green" />
          </section>
          <section className="content-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">FRESH OFF THE LIST</p>
                <h2>Recently added</h2>
              </div>
              <Link className="text-link" to="/tasks">View all tasks <span aria-hidden="true">→</span></Link>
            </div>
            <TaskList tasks={tasks} />
          </section>
          <section className="note-card">
            <div className="note-icon" aria-hidden="true">✳</div>
            <div>
              <strong>Progress, not perfection.</strong>
              <p>Break your next big thing into one small, doable step.</p>
            </div>
            <Link className="button button-outline button-small" to="/tasks/new">Add a task</Link>
          </section>
        </>
      )}
    </div>
  );
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}
