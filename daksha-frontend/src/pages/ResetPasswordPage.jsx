// src/pages/ResetPasswordPage.jsx
// Landing page for the password-reset email link. Supabase turns the link into
// a short-lived recovery session (detectSessionInUrl); here the user picks a
// new password. Expired or already-used links get a clear way to request a new one.
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock } from "lucide-react";

import { supabase } from "../lib/supabaseClient";
import {
  AuthShell, Notice, PasswordField, SubmitButton, TextLink,
} from "../components/auth/AuthUI";
import { describeAuthError, MIN_PASSWORD } from "../lib/authErrors";

function linkErrorFromUrl() {
  const raw = (window.location.hash || "").replace(/^#/, "") + "&" + (window.location.search || "").replace(/^\?/, "");
  const p = new URLSearchParams(raw);
  const desc = p.get("error_description");
  return desc ? desc.replace(/\+/g, " ") : null;
}

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const pwRef = useRef(null);
  const confirmRef = useRef(null);
  const [pwLen, setPwLen] = useState(0);
  const [linkError] = useState(linkErrorFromUrl);
  const [status, setStatus] = useState(() => (linkError ? "invalid" : "checking")); // checking | ready | invalid
  const [notice, setNotice] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (linkError) return undefined;
    let settled = false;
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "PASSWORD_RECOVERY" || (session && !settled)) { settled = true; setStatus("ready"); }
    });
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) { settled = true; setStatus("ready"); }
    });
    // Give the URL token a moment to be exchanged before calling the link dead.
    const t = setTimeout(() => { if (!settled) setStatus("invalid"); }, 4000);
    return () => { clearTimeout(t); subscription.unsubscribe(); };
  }, [linkError]);

  const onSubmit = async (e) => {
    e.preventDefault();
    const pw = pwRef.current.value;
    if (pw.length < MIN_PASSWORD) {
      setNotice({ tone: "error", title: "Choose a stronger password", message: `Use at least ${MIN_PASSWORD} characters.` });
      return pwRef.current.focus();
    }
    if (pw !== confirmRef.current.value) {
      setNotice({ tone: "error", title: "Passwords don't match", message: "Type the same password in both boxes." });
      return confirmRef.current.focus();
    }
    setLoading(true);
    setNotice(null);
    const { error } = await supabase.auth.updateUser({ password: pw });
    setLoading(false);
    if (error) {
      const d = describeAuthError(error);
      return setNotice({ tone: "error", title: d.title, message: d.message });
    }
    pwRef.current.value = "";
    confirmRef.current.value = "";
    // Sign out the recovery session so the user signs in fresh with the new password.
    await supabase.auth.signOut();
    navigate("/login", { replace: true, state: { notice: "password-updated" } });
  };

  if (status === "checking") {
    return <AuthShell subtitle="Reset password"><p className="text-center text-sm text-gray-500">Checking your link…</p></AuthShell>;
  }

  if (status === "invalid") {
    return (
      <AuthShell subtitle="Reset password"
        footer={<TextLink onClick={() => navigate("/login")}>Back to sign in</TextLink>}>
        <div className="space-y-6">
          <Notice tone="error" title="This reset link has expired or was already used"
            actions={[{ label: "Send a new link", onClick: () => navigate("/forgot-password") }]}>
            {linkError ? `${linkError}. ` : ""}Reset links work once and expire after a short time.
          </Notice>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell subtitle="Choose a new password">
      <form onSubmit={onSubmit} className="space-y-6">
        {notice && <Notice {...notice} />}
        <PasswordField ref={pwRef} icon={Lock} label="New password" required autoFocus
          autoComplete="new-password" minLength={MIN_PASSWORD} onLengthChange={setPwLen}
          hint={pwLen > 0 && pwLen < MIN_PASSWORD ? `${MIN_PASSWORD - pwLen} more characters needed` : `At least ${MIN_PASSWORD} characters`} />
        <PasswordField ref={confirmRef} icon={Lock} label="Confirm new password" required
          autoComplete="new-password" />
        <SubmitButton loading={loading} loadingText="Saving…">Save new password</SubmitButton>
      </form>
    </AuthShell>
  );
}
