// src/lib/authErrors.js
// Turns Supabase auth errors into plain-language guidance for the auth screens.

export const MIN_PASSWORD = 8;

/**
 * Map a Supabase auth error to { kind, title, message }.
 * `kind` lets screens attach the right actions (sign in, reset, resend...).
 */
export function describeAuthError(err) {
  const code = err?.code || "";
  const msg = (err?.message || "").toLowerCase();
  const status = err?.status;

  if (code === "user_already_exists" || code === "email_exists" || msg.includes("already registered"))
    return { kind: "exists", title: "This email already has an account",
             message: "Sign in with it instead, or reset the password if you've forgotten it." };
  if (code === "invalid_credentials" || msg.includes("invalid login credentials"))
    return { kind: "credentials", title: "Email or password is incorrect",
             message: "Check both and try again. Passwords are case-sensitive." };
  if (code === "email_not_confirmed" || msg.includes("email not confirmed"))
    return { kind: "unconfirmed", title: "Confirm your email first",
             message: "Open the confirmation link we emailed you, then sign in." };
  if (code === "weak_password" || msg.includes("password should"))
    return { kind: "weak", title: "Choose a stronger password",
             message: err?.message || `Use at least ${MIN_PASSWORD} characters.` };
  if (code === "same_password")
    return { kind: "weak", title: "That's your current password", message: "Pick a new one." };
  if (code.startsWith("over_") || status === 429 || msg.includes("rate limit"))
    return { kind: "rate", title: "Too many attempts",
             message: "Please wait a minute before trying again." };
  if (code === "signup_disabled")
    return { kind: "other", title: "Sign-ups are closed", message: "New accounts can't be created right now." };
  if (code === "validation_failed" && msg.includes("email"))
    return { kind: "other", title: "Check your email address", message: err?.message };
  if (err?.name === "AuthRetryableFetchError" || msg.includes("failed to fetch") || msg.includes("network"))
    return { kind: "network", title: "Can't reach the server",
             message: "Check your internet connection and try again." };
  return { kind: "other", title: "Something went wrong", message: err?.message || "Please try again." };
}
