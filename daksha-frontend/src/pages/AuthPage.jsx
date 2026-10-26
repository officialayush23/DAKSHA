// src/pages/AuthPage.jsx
// Sign in, register and forgot-password for customers (and sign in for admins
// at /admin/login). Errors are shown inline with a next step, never just a
// toast, and the password is never placed in React state or the DOM.
import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { User, Lock, Mail, Phone } from "lucide-react";

import { supabase } from "../lib/supabaseClient";
import { SessionService } from "../lib/api";
import {
  AuthShell, Notice, Field, PasswordField, SubmitButton, TextLink,
} from "../components/auth/AuthUI";
import { describeAuthError, MIN_PASSWORD } from "../lib/authErrors";

const RESEND_COOLDOWN_S = 60;
const origin = typeof window !== "undefined" ? window.location.origin : "";

function useCooldown() {
  const [left, setLeft] = useState(0);
  useEffect(() => {
    if (left <= 0) return undefined;
    const t = setTimeout(() => setLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [left]);
  return [left, () => setLeft(RESEND_COOLDOWN_S)];
}

export default function AuthPage({ mode: modeProp, isRegister = false }) {
  const mode = modeProp || (isRegister ? "register" : "login");
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const isAdmin = location.pathname.startsWith("/admin");

  const [email, setEmail] = useState(location.state?.email || "");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pwLen, setPwLen] = useState(0);
  const passwordRef = useRef(null);
  const emailRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [notice, setNotice] = useState(null);       // { tone, title, message, actions }
  const [sentTo, setSentTo] = useState("");          // confirmation / reset email sent to
  const [cooldown, startCooldown] = useCooldown();

  // Messages carried in from other screens or from email links.
  useEffect(() => {
    const s = location.state?.notice;
    if (params.get("confirmed")) {
      setNotice({ tone: "success", title: "Email confirmed", message: "Sign in to continue." });
    } else if (s === "exists") {
      setNotice({ tone: "info", title: "You already have an account", message: "Sign in with your password below." });
    } else if (s === "password-updated") {
      setNotice({ tone: "success", title: "Password updated", message: "Sign in with your new password." });
    } else if (s === "session-expired") {
      setNotice({ tone: "info", title: "Please sign in again", message: "Your session ended." });
    }
    // reset per-screen state when switching between login / register / forgot
    setSentTo("");
    if (passwordRef.current) passwordRef.current.value = "";
    setPwLen(0);
    if (!s && !params.get("confirmed")) setNotice(null);
  }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps

  const go = (path, state) => navigate(path, { state: { email, ...state } });

  const showError = (err) => {
    const d = describeAuthError(err);
    const actions = [];
    if (d.kind === "exists") {
      actions.push({ label: "Sign in instead", onClick: () => go("/login", { notice: "exists" }) });
      actions.push({ label: "Reset password", onClick: () => go("/forgot-password") });
    } else if (d.kind === "credentials") {
      actions.push({ label: "Forgot password?", onClick: () => go("/forgot-password") });
      if (!isAdmin) actions.push({ label: "Create an account", onClick: () => go("/register") });
    } else if (d.kind === "unconfirmed") {
      actions.push({ label: "Resend confirmation email", onClick: resendConfirmation });
    }
    setNotice({ tone: "error", title: d.title, message: d.message, actions });
    if (d.kind === "credentials" || d.kind === "weak") passwordRef.current?.focus();
  };

  // Start the backend session. A sleeping Render instance can take ~30-50 s to
  // wake, so say so instead of leaving a spinner with no explanation.
  const startBackendSession = async () => {
    const slow = setTimeout(
      () => setLoadingText("Waking up the store server… the first sign-in can take up to a minute"), 4000);
    try {
      await SessionService.start("web");
    } catch {
      toast.warning("Signed in. Some features may take a moment to load.");
    } finally {
      clearTimeout(slow);
    }
  };

  const finishSignedIn = async (welcome) => {
    if (passwordRef.current) passwordRef.current.value = "";
    if (isAdmin) {
      navigate(location.state?.from?.pathname || "/admin", { replace: true });
      return;
    }
    setLoadingText("Setting up your session…");
    await startBackendSession();
    toast.success(welcome);
    navigate("/dash/shop", { replace: true });
  };

  async function resendConfirmation() {
    if (!email) { emailRef.current?.focus(); return; }
    const { error } = await supabase.auth.resend({
      type: "signup", email, options: { emailRedirectTo: `${origin}/login?confirmed=1` },
    });
    if (error) return showError(error);
    startCooldown();
    setNotice({ tone: "success", title: "Confirmation email sent", message: `Check ${email} (and your spam folder).` });
  }

  const handleLogin = async () => {
    const { error } = await supabase.auth.signInWithPassword({ email, password: passwordRef.current.value });
    if (error) return showError(error);
    await finishSignedIn("Welcome back");
  };

  const handleRegister = async () => {
    const password = passwordRef.current.value;
    if (password.length < MIN_PASSWORD) {
      setNotice({ tone: "error", title: "Choose a stronger password", message: `Use at least ${MIN_PASSWORD} characters.` });
      passwordRef.current.focus();
      return;
    }
    const { data, error } = await supabase.auth.signUp({
      email, password,
      options: { data: { name: name.trim(), phone: phone.trim() }, emailRedirectTo: `${origin}/login?confirmed=1` },
    });
    if (error) return showError(error);
    // With email confirmation ON, Supabase hides existing accounts behind a fake
    // user with no identities instead of returning an error.
    if (data?.user && Array.isArray(data.user.identities) && data.user.identities.length === 0) {
      return showError({ code: "user_already_exists" });
    }
    if (!data.session) {
      if (passwordRef.current) passwordRef.current.value = "";
      setSentTo(email);
      startCooldown();
      return;
    }
    await finishSignedIn("Account created. Welcome!");
  };

  const handleForgot = async () => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: `${origin}/reset-password` });
    if (error && describeAuthError(error).kind !== "other") return showError(error);
    // Same message whether or not the account exists, so the form can't be
    // used to discover who has an account.
    setSentTo(email);
    startCooldown();
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setNotice(null);
    setLoading(true);
    setLoadingText(mode === "register" ? "Creating your account…" : mode === "forgot" ? "Sending link…" : "Signing in…");
    try {
      if (mode === "register") await handleRegister();
      else if (mode === "forgot") await handleForgot();
      else await handleLogin();
    } catch (err) {
      showError(err);
    } finally {
      setLoading(false);
    }
  };

  // ── "Check your email" screens ───────────────────────────────────────────
  if (sentTo) {
    const isReset = mode === "forgot";
    return (
      <AuthShell subtitle={isReset ? "Reset password" : "Almost there"}>
        <div className="text-center space-y-6">
          <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mx-auto">
            <Mail className="text-white w-7 h-7" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xl font-serif mb-2">Check your email</h2>
            <p className="text-sm text-gray-500">
              {isReset
                ? <>If an account exists for <strong>{sentTo}</strong>, we've sent a link to reset the password.</>
                : <>We sent a confirmation link to <strong>{sentTo}</strong>. Open it to activate your account.</>}
              <br />It can take a minute; check spam too.
            </p>
          </div>
          {notice && <Notice {...notice} />}
          <button type="button" disabled={cooldown > 0}
            onClick={isReset ? () => { setEmail(sentTo); handleForgot(); } : resendConfirmation}
            className="w-full border border-black py-3 uppercase text-xs tracking-[0.2em] disabled:opacity-40">
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend email"}
          </button>
          <div className="flex justify-center gap-6">
            <TextLink onClick={() => setSentTo("")}>Use a different email</TextLink>
            <TextLink onClick={() => go("/login")}>Back to sign in</TextLink>
          </div>
        </div>
      </AuthShell>
    );
  }

  // ── Forms ────────────────────────────────────────────────────────────────
  const subtitle = isAdmin ? "Admin access"
    : mode === "register" ? "Begin your journey"
    : mode === "forgot" ? "Reset your password"
    : "Member access";

  const footer = isAdmin ? null : mode === "register" ? (
    <TextLink onClick={() => go("/login")}>Already a member? Sign in</TextLink>
  ) : mode === "forgot" ? (
    <TextLink onClick={() => go("/login")}>Remembered it? Sign in</TextLink>
  ) : (
    <TextLink onClick={() => go("/register")}>New here? Create an account</TextLink>
  );

  return (
    <AuthShell subtitle={subtitle} footer={footer}>
      <form onSubmit={onSubmit} className="space-y-6">
        {notice && <Notice {...notice} />}

        {mode === "forgot" && (
          <p className="text-sm text-gray-500">Enter the email you signed up with and we'll send you a link to choose a new password.</p>
        )}

        {mode === "register" && (
          <>
            <Field icon={User} label="Full name" required autoComplete="name" autoFocus
              value={name} onChange={(e) => setName(e.target.value)} />
            <Field icon={Phone} label="Phone (for order updates)" required type="tel" inputMode="tel"
              autoComplete="tel" pattern="^\+?[0-9][0-9 ]{9,14}$"
              title="10-digit mobile number, optionally with country code"
              value={phone} onChange={(e) => setPhone(e.target.value)} />
          </>
        )}

        <Field ref={emailRef} icon={Mail} label="Email" required type="email" autoComplete="email"
          inputMode="email" autoFocus={mode !== "register"}
          value={email} onChange={(e) => setEmail(e.target.value.trim())} />

        {mode !== "forgot" && (
          <div className="space-y-2">
            <PasswordField ref={passwordRef} icon={Lock} required
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              minLength={mode === "register" ? MIN_PASSWORD : undefined}
              onLengthChange={setPwLen}
              hint={mode === "register"
                ? (pwLen > 0 && pwLen < MIN_PASSWORD ? `${MIN_PASSWORD - pwLen} more characters needed` : `At least ${MIN_PASSWORD} characters`)
                : undefined} />
            {mode === "login" && (
              <div className="text-right">
                <TextLink onClick={() => go("/forgot-password")}>Forgot password?</TextLink>
              </div>
            )}
          </div>
        )}

        <SubmitButton loading={loading} loadingText={loadingText}>
          {mode === "register" ? "Create account" : mode === "forgot" ? "Send reset link" : "Sign in"}
        </SubmitButton>
      </form>
    </AuthShell>
  );
}
