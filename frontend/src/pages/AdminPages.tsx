import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import {
  getAdminStatistics,
  listAdminUsers,
  updateAccountRole,
  updateAccountStatus,
} from "../api/users";
import { useAuth } from "../auth/AuthContext";
import { ErrorMessage, Loading, PageHeader, StatCard } from "../components/Shared";
import type { AdminStatistics, AdminUser } from "../types";

const PAGE_SIZE = 20;

export function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setStats(await getAdminStatistics());
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load system statistics.");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="ADMINISTRATION"
        title="System overview"
        subtitle="A high-level view of accounts and task activity."
      />
      {error && <ErrorMessage message={error} onRetry={() => void load()} />}
      {loading ? <Loading label="Loading system statistics…" /> : stats && (
        <>
          <section className="stats-grid" aria-label="System statistics">
            <StatCard label="Total people" value={stats.total_users} accent="accent-ink" note={`${stats.active_users} active`} />
            <StatCard label="Administrators" value={stats.total_admins} accent="accent-blue" />
            <StatCard label="All tasks" value={stats.total_tasks} accent="accent-amber" />
            <StatCard label="Completed" value={stats.completed_tasks} accent="accent-green" note={`${stats.pending_tasks} to do · ${stats.in_progress_tasks} in progress`} />
          </section>
          <section className="admin-callout">
            <div className="note-icon" aria-hidden="true">♙</div>
            <div>
              <h2>People & access</h2>
              <p>Review account activity and manage roles. Admin access never grants access to anyone's private tasks.</p>
            </div>
            <Link className="button button-primary button-small" to="/admin/users">Manage users <span aria-hidden="true">→</span></Link>
          </section>
          <section className="content-section">
            <div className="section-heading">
              <div><p className="eyebrow">ACCOUNT STATUS</p><h2>People at a glance</h2></div>
            </div>
            <div className="compact-stats">
              <div><span className="stat-dot accent-green" />Active accounts <strong>{stats.active_users}</strong></div>
              <div><span className="stat-dot accent-amber" />Inactive accounts <strong>{stats.inactive_users}</strong></div>
              <div><span className="stat-dot accent-blue" />Tasks in progress <strong>{stats.in_progress_tasks}</strong></div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export function AdminUsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<boolean | "">("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await listAdminUsers({
        search,
        role: roleFilter,
        is_active: activeFilter,
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,
      });
      setUsers(result.slice(0, PAGE_SIZE));
      setHasMore(result.length > PAGE_SIZE);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not load users.");
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, activeFilter, page]);
  useEffect(() => { void load(); }, [load]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(0);
    setSearch(searchInput.trim());
  }

  async function toggleActive(account: AdminUser) {
    const verb = account.is_active ? "deactivate" : "activate";
    if (!window.confirm(`Are you sure you want to ${verb} ${account.full_name}?`)) return;
    setError("");
    setNotice("");
    try {
      await updateAccountStatus(account.id, !account.is_active);
      setNotice(`${account.full_name}'s account was ${account.is_active ? "deactivated" : "activated"}.`);
      await load();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update account status.");
    }
  }

  async function toggleRole(account: AdminUser) {
    const nextRole = account.role === "admin" ? "user" : "admin";
    if (!window.confirm(`Change ${account.full_name}'s role to ${nextRole}?`)) return;
    setError("");
    setNotice("");
    try {
      await updateAccountRole(account.id, nextRole);
      setNotice(`${account.full_name}'s role was changed to ${nextRole}.`);
      await load();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update account role.");
    }
  }

  return (
    <div className="page-content">
      <PageHeader
        eyebrow="ADMINISTRATION"
        title="People"
        subtitle="Review accounts and manage access with care."
      />
      <section className="filter-panel admin-filter">
        <form className="search-form" onSubmit={submitSearch}>
          <label className="sr-only" htmlFor="people-search">Search users</label>
          <span aria-hidden="true">⌕</span>
          <input
            id="people-search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by name or email"
          />
          <button className="button button-secondary button-small">Search</button>
        </form>
        <label className="filter-control">
            <span>Role</span>
            <select value={roleFilter} onChange={(event) => { setPage(0); setRoleFilter(event.target.value); }}>
              <option value="">All roles</option>
              <option value="user">Member</option>
              <option value="admin">Administrator</option>
            </select>
          </label>
          <label className="filter-control">
            <span>Account status</span>
          <select
            value={activeFilter === "" ? "" : String(activeFilter)}
            onChange={(event) => {
              setPage(0);
              setActiveFilter(event.target.value === "" ? "" : event.target.value === "true");
            }}
          >
            <option value="">All accounts</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </label>
      </section>
      {notice && <p className="alert alert-success" role="status">{notice}</p>}
      {error && <ErrorMessage message={error} onRetry={() => void load()} />}
      <section className="content-section">
        <div className="section-heading">
          <div><p className="eyebrow">ACCOUNT DIRECTORY</p><h2>{search ? `Search results` : "All people"}</h2></div>
          <span className="result-count">{loading ? "Loading…" : `${users.length}${hasMore ? "+" : ""} shown`}</span>
        </div>
        {loading ? <Loading label="Loading users…" /> : users.length === 0 ? (
          <div className="empty-state"><span className="empty-icon">♙</span><h3>No accounts found</h3><p>Try a different search or status filter.</p></div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Person</th><th>Role</th><th>Tasks</th><th>Status</th><th><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {users.map((account) => (
                  <tr key={account.id}>
                    <td>
                      <div className="person-cell">
                        <span className="avatar">{account.full_name.slice(0, 1).toUpperCase()}</span>
                        <span><strong>{account.full_name}{account.id === user?.id && <small className="you-label">YOU</small>}</strong><small>{account.email}</small></span>
                      </div>
                    </td>
                    <td><span className={`role-tag role-${account.role}`}>{account.role}</span></td>
                    <td>{account.task_count}</td>
                    <td><span className={`account-status ${account.is_active ? "is-active" : "is-inactive"}`}><span />{account.is_active ? "Active" : "Inactive"}</span></td>
                    <td>
                      <div className="table-actions">
                        <button className="text-button" type="button" onClick={() => void toggleRole(account)}>
                          {account.role === "admin" ? "Make member" : "Make admin"}
                        </button>
                        <button className="text-button" type="button" onClick={() => void toggleActive(account)}>
                          {account.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="admin-permission-note">Account and role actions are checked by the API. The last active administrator cannot be deactivated or demoted.</p>
          </div>
        )}
      </section>
      <div className="pagination">
        <button className="button button-outline button-small" disabled={page === 0 || loading} onClick={() => setPage((value) => Math.max(0, value - 1))}>← Previous</button>
        <span>Page {page + 1}</span>
        <button className="button button-outline button-small" disabled={!hasMore || loading} onClick={() => setPage((value) => value + 1)}>Next →</button>
      </div>
    </div>
  );
}
