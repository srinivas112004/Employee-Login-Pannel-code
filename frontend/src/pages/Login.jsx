// src/pages/Login.jsx
import React, { useState } from "react";
import { Link } from "react-router-dom";
import API from "../api"; // your axios instance (keeps working with tryAlternateLogins)
import { useAuth } from "../context/AuthContext";
import VerifyOTP from "../components/VerifyOTP";

export default function Login() {
  const { login, getProfile } = useAuth();

  const [form, setForm] = useState({ email: "", password: "", remember: false });
  const [error, setError] = useState("");
  const [tryingAlternate, setTryingAlternate] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [sending2FA, setSending2FA] = useState(false);

  const onChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  // Normalize tokens returned by various backends
  function extractTokens(data) {
    if (!data) return null;
    // common shapes
    if (data.tokens && (data.tokens.access || data.tokens.refresh)) {
      return { access: data.tokens.access, refresh: data.tokens.refresh, user: data.user || null };
    }
    if (data.access) {
      return { access: data.access, refresh: data.refresh || null, user: data.user || null };
    }
    if (data.token || data.auth_token) {
      return { access: data.token || data.auth_token, refresh: null, user: data.user || null };
    }
    if (data.access_token) {
      return { access: data.access_token, refresh: data.refresh_token || null, user: data.user || null };
    }
    // Sometimes backend returns { access: "...", refresh: "..." } nested under data.data, etc.
    if (data.data) return extractTokens(data.data);
    return null;
  }

  // Try a list of possible auth endpoints & payloads until one works
  async function tryAlternateLogins(email, password) {
    setTryingAlternate(true);
    const endpoints = [
      { url: "/auth/login/", payload: (e, p) => ({ email: e, password: p }) },
      { url: "/auth/login/", payload: (e, p) => ({ username: e, password: p }) },
      { url: "/auth/token/", payload: (e, p) => ({ email: e, password: p }) },
      { url: "/auth/token/", payload: (e, p) => ({ username: e, password: p }) },
      { url: "/token/", payload: (e, p) => ({ username: e, password: p }) },
      { url: "/api/token/", payload: (e, p) => ({ username: e, password: p }) },
      { url: "/api/token/", payload: (e, p) => ({ email: e, password: p }) },
      { url: "/auth/token/obtain/", payload: (e, p) => ({ email: e, password: p }) },
      { url: "/auth/token/obtain/", payload: (e, p) => ({ username: e, password: p }) },
    ];

    for (const ep of endpoints) {
      try {
        const res = await API.post(ep.url, ep.payload(email, password));
        // If backend returns requires_2fa, stop and surface to UI
        if (res.data && res.data.requires_2fa) {
          setRequires2FA(true);
          setUserEmail(res.data.email || email);
          setTryingAlternate(false);
          return "2fa"; // signal 2fa required
        }

        const tokens = extractTokens(res.data);
        if (tokens && tokens.access) {
          // Save tokens in the same keys AuthContext expects
          localStorage.setItem("access_token", tokens.access);
          if (tokens.refresh) localStorage.setItem("refresh_token", tokens.refresh);
          if (tokens.user) {
            localStorage.setItem("user", JSON.stringify(tokens.user));
          } else {
            // try to fetch profile if user not included
            try {
              const p = await getProfile();
              if (p) localStorage.setItem("user", JSON.stringify(p));
            } catch (e) {
              // ignore profile fetch failure here
            }
          }
          setTryingAlternate(false);
          return true;
        }
      } catch (err) {
        // if network error, stop and bubble up
        if (!err.response) {
          setTryingAlternate(false);
          throw new Error("Network error contacting backend.");
        }
        // otherwise try next endpoint
      }
    }

    setTryingAlternate(false);
    return false;
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSending2FA(false);

    if (!form.email || !form.password) {
      setError("Please provide email/username and password.");
      return;
    }

    setSending2FA(true);

    try {
      // Primary attempt: call your usual login endpoint
      const res = await API.post("/auth/login/", { email: form.email, password: form.password });

      // If backend says 2FA required on primary attempt
      if (res.data?.requires_2fa) {
        setSending2FA(false);
        setRequires2FA(true);
        setUserEmail(res.data.email || form.email);
        return;
      }

      // Try to extract tokens from primary response if present
      const tokens = extractTokens(res.data);
      if (tokens && tokens.access) {
        // Save tokens and refresh profile via AuthContext
        localStorage.setItem("access_token", tokens.access);
        if (tokens.refresh) localStorage.setItem("refresh_token", tokens.refresh);
        if (tokens.user) localStorage.setItem("user", JSON.stringify(tokens.user));
        try {
          // use AuthContext.getProfile to sync user state
          await getProfile();
        } catch (e) {
          // ignore profile fetch error
        }
        // AuthContext.login also handles redirect; but since we directly stored tokens we can call login to run its logic
        try {
          await login(form.email, form.password);
        } catch (_) {
          // login() in context expects to call API; if it fails we already set tokens — just redirect
          window.location.href = "/dashboard";
        }
        return;
      }

      // If primary didn't return tokens, fallback to alternate endpoints
      const alt = await tryAlternateLogins(form.email, form.password);
      if (alt === "2fa") {
        // 2FA flow started by alternate endpoint
        return;
      }
      if (alt === true) {
        // tokens saved by tryAlternateLogins; call login() to let AuthContext finalize (optional)
        try {
          await login(form.email, form.password);
        } catch (_) {
          window.location.href = "/dashboard";
        }
        return;
      }

      // if nothing worked, show friendly backend message if present
      const backendMsg =
        res?.data?.non_field_errors?.[0] ||
        res?.data?.detail ||
        res?.data?.message ||
        "Login failed. Please check credentials.";
      setError(backendMsg);
    } catch (err) {
      // Primary request failed, try alternate endpoints
      try {
        const altResult = await tryAlternateLogins(form.email, form.password);
        if (altResult === "2fa") return;
        if (altResult === true) {
          try {
            await login(form.email, form.password);
          } catch (_) {
            window.location.href = "/dashboard";
          }
          return;
        }

        // show backend error from original failure if present
        const backendMsg =
          err?.response?.data?.non_field_errors?.[0] ||
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          "Login failed. Please check credentials or contact admin.";
        setError(backendMsg);
      } catch (networkErr) {
        setError(networkErr.message || "Network error. Please check server.");
      }
    } finally {
      setSending2FA(false);
      setTryingAlternate(false);
    }
  };

  // When 2FA verification completes, backend returns tokens+user in that response
  const handle2FAVerified = async (data) => {
    const tokens = extractTokens(data);
    if (tokens && tokens.access) {
      localStorage.setItem("access_token", tokens.access);
      if (tokens.refresh) localStorage.setItem("refresh_token", tokens.refresh);
      if (tokens.user) localStorage.setItem("user", JSON.stringify(tokens.user));
      try {
        await getProfile();
      } catch (e) {
        // ignore profile refresh failure
      }
      // After storing tokens, call login() to let AuthContext update and redirect as needed
      try {
        await login(tokens.user?.email || form.email, form.password);
      } catch (e) {
        window.location.href = "/dashboard";
      }
    } else {
      setError("Verification succeeded but tokens not received. Contact admin.");
    }
  };

  // Show 2FA UI when required
  if (requires2FA) {
    return (
      <div className="container d-flex align-items-center justify-content-center vh-100" style={{ background: "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)" }}>
        <div className="card p-4 shadow-lg rounded-4 border-0" style={{ width: 560 }}>
          <div className="mb-3">
            <h4>Two-Factor Authentication</h4>
            <small className="text-muted">Enter the code sent to your email</small>
          </div>
          <div className="alert alert-info mb-3">
            We've sent a 6-digit code to <strong>{userEmail}</strong>
          </div>

          <VerifyOTP email={userEmail} purpose="login_2fa" onVerified={handle2FAVerified} />

          <div className="text-center mt-3">
            <button className="btn btn-link" onClick={() => { setRequires2FA(false); setError(""); }}>
              ← Back to login
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isBusy = sending2FA || tryingAlternate;

  return (
    <div className="container d-flex align-items-center justify-content-center vh-100" style={{ background: "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)" }}>
      <div className="card p-4 shadow-lg rounded-4 border-0" style={{ width: 460 }}>
        <div className="mb-3 d-flex align-items-center">
          <div className="me-3"><i className="bi bi-shield-lock-fill text-primary" style={{ fontSize: 28 }}></i></div>
          <div>
            <h4 className="mb-0">Employee Login</h4>
            <small className="text-muted">Secure sign in to access your dashboard</small>
          </div>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={onSubmit} noValidate>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email or Username</label>
            <div className="input-group input-group-lg">
              <span className="input-group-text bg-white"><i className="bi bi-envelope-fill"></i></span>
              <input id="email" name="email" type="text" className="form-control rounded-pill" value={form.email} onChange={onChange} placeholder="employee@company.com" required />
            </div>
          </div>

          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="input-group input-group-lg">
              <span className="input-group-text bg-white"><i className="bi bi-lock-fill"></i></span>
              <input id="password" name="password" type={showPassword ? "text" : "password"} className="form-control rounded-pill" value={form.password} onChange={onChange} placeholder="••••••••" required />
              <button type="button" className="btn btn-outline-secondary border-0" onClick={() => setShowPassword((s) => !s)} style={{ marginLeft: -40 }}>
                <i className={`bi ${showPassword ? "bi-eye-slash-fill" : "bi-eye-fill"}`}></i>
              </button>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center mb-3">
            <div className="form-check">
              <input id="remember" name="remember" className="form-check-input" type="checkbox" checked={form.remember} onChange={onChange} />
              <label className="form-check-label" htmlFor="remember">Remember me</label>
            </div>
            <Link to="/password-reset" className="small">Forgot password?</Link>
          </div>

          <div className="d-grid">
            <button type="submit" className="btn btn-primary btn-lg rounded-pill" disabled={isBusy} aria-disabled={isBusy}>
              {isBusy ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  {sending2FA ? "Sending verification code..." : "Logging in..."}
                </>
              ) : "Login"}
            </button>
          </div>
        </form>

        <hr className="my-4" />

        <div className="text-center"><small className="text-muted">Don't have access? Contact your HR department.</small></div>
      </div>

      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" />
    </div>
  );
}
