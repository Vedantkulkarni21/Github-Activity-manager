import { Navigate } from "react-router-dom";
import { Github, CircleDot, Cog, Slack } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";

export default function Login() {
  const { user, loading } = useAuth();

  if (loading) return <div className="center-page">Loading…</div>;
  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1 className="login-title">Repo Bot</h1>
        <p className="login-subtitle">
          Connect a repository, define a few rules, and let the bot label issues,
          comment, and post to Slack for you — automatically.
        </p>

        <div className="login-pipeline">
          <div className="login-pipeline-node"><CircleDot size={18} /></div>
          <span>→</span>
          <div className="login-pipeline-node"><Cog size={18} /></div>
          <span>→</span>
          <div className="login-pipeline-node"><Slack size={18} /></div>
        </div>

        <a className="github-btn" href={api.githubLoginUrl()}>
          <Github size={17} /> Sign in with GitHub
        </a>
      </div>
    </div>
  );
}
