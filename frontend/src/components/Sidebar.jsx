import { NavLink } from "react-router-dom";
import { LayoutGrid, GitBranch, ListChecks, Zap } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">
          <Zap size={15} color="#fff" strokeWidth={2.5} />
        </div>
        <span className="sidebar-brand-name">Repo Bot</span>
      </div>

      <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
        <LayoutGrid size={16} /> Event log
      </NavLink>
      <NavLink to="/repos" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
        <GitBranch size={16} /> Repositories
      </NavLink>
      <NavLink to="/rules" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
        <ListChecks size={16} /> Rules
      </NavLink>

      {user && (
        <div className="sidebar-footer">
          {user.avatar_url ? (
            <img className="avatar" src={user.avatar_url} alt="" />
          ) : (
            <div className="avatar" />
          )}
          <div className="sidebar-user">
            <span className="sidebar-user-name">{user.username}</span>
            <button className="logout-btn" onClick={logout}>Sign out</button>
          </div>
        </div>
      )}
    </aside>
  );
}
