// src/components/auth/AuthUI.jsx
// Shared building blocks for the sign-in, register, forgot-password and
// reset-password screens: layout shell, inline notices, inputs, and a single
// place that turns Supabase auth errors into plain-language guidance.
import React, { forwardRef, useId, useState } from "react";
import { Eye, EyeOff, AlertCircle, CheckCircle2, Info, Loader2 } from "lucide-react";

export function AuthShell({ subtitle, children, footer }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FDFDFD] px-4">
      <div className="w-full max-w-md py-10">
        <div className="text-center mb-10">
          <a href="/" className="inline-block text-5xl font-serif mb-2 tracking-tighter">Daksha</a>
          {subtitle && (
            <p className="text-xs uppercase tracking-[0.3em] text-gray-400">{subtitle}</p>
          )}
        </div>
        {children}
        {footer && <div className="mt-8 text-center space-y-3">{footer}</div>}
      </div>
    </div>
  );
}

const TONES = {
  error:   { box: "border-red-200 bg-red-50 text-red-800",         Icon: AlertCircle },
  info:    { box: "border-gray-200 bg-gray-50 text-gray-700",      Icon: Info },
  success: { box: "border-emerald-200 bg-emerald-50 text-emerald-800", Icon: CheckCircle2 },
};

/** Inline, screen-reader-announced message with optional action buttons. */
export function Notice({ tone = "info", title, message, children, actions }) {
  const { box, Icon } = TONES[tone] || TONES.info;
  return (
    <div role={tone === "error" ? "alert" : "status"} aria-live="polite"
      className={`border rounded-md px-4 py-3 text-sm flex gap-3 ${box}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
      <div className="space-y-1 min-w-0">
        {title && <p className="font-medium">{title}</p>}
        {(message || children) && <div className="leading-relaxed">{message}{children}</div>}
        {actions?.length > 0 && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 pt-1">
            {actions.map((a) => (
              <button key={a.label} type="button" onClick={a.onClick}
                className="underline underline-offset-2 font-medium hover:opacity-70">
                {a.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Underlined text input with a leading icon and an accessible label. */
export const Field = forwardRef(function Field({ icon: Icon, label, hint, invalid, ...props }, ref) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="sr-only">{label}</label>
      <div className="relative">
        {Icon && <Icon className="absolute left-0 top-3 text-gray-300 w-5 h-5" aria-hidden="true" />}
        <input id={id} ref={ref} placeholder={label} aria-invalid={invalid || undefined}
          aria-describedby={hint ? `${id}-hint` : undefined}
          className={`w-full pl-8 border-b py-3 outline-none font-serif bg-transparent focus:border-black transition-colors ${
            invalid ? "border-red-400" : "border-gray-200"}`}
          {...props} />
      </div>
      {hint && <p id={`${id}-hint`} className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  );
});

/**
 * Password input that is deliberately UNCONTROLLED: no `value` prop, so React
 * never mirrors the typed password into the DOM `value` attribute (where dev
 * tools, console warnings and extensions could read it). Read it from the ref
 * at submit time. `onLengthChange` reports only the length, never the text.
 */
export const PasswordField = forwardRef(function PasswordField(
  { icon, label = "Password", hint, invalid, onLengthChange, ...props }, ref) {
  const [visible, setVisible] = useState(false);
  const id = useId();
  const Icon = icon;
  return (
    <div>
      <label htmlFor={id} className="sr-only">{label}</label>
      <div className="relative">
        {Icon && <Icon className="absolute left-0 top-3 text-gray-300 w-5 h-5" aria-hidden="true" />}
        <input id={id} ref={ref} type={visible ? "text" : "password"} placeholder={label}
          spellCheck={false} autoCapitalize="none" autoCorrect="off"
          aria-invalid={invalid || undefined}
          aria-describedby={hint ? `${id}-hint` : undefined}
          onChange={(e) => onLengthChange?.(e.target.value.length)}
          className={`w-full pl-8 pr-10 border-b py-3 outline-none font-serif bg-transparent focus:border-black transition-colors ${
            invalid ? "border-red-400" : "border-gray-200"}`}
          {...props} />
        <button type="button" onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"} aria-pressed={visible}
          className="absolute right-0 top-2.5 p-1 text-gray-400 hover:text-black">
          {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
      {hint && <p id={`${id}-hint`} className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  );
});

export function SubmitButton({ loading, loadingText = "Please wait…", children, ...props }) {
  return (
    <button type="submit" disabled={loading} aria-busy={loading}
      className="w-full bg-black text-white py-4 uppercase text-xs tracking-[0.2em] disabled:opacity-60 flex items-center justify-center gap-2"
      {...props}>
      {loading && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
      {loading ? loadingText : children}
    </button>
  );
}

export function TextLink({ children, ...props }) {
  return (
    <button type="button" className="text-xs text-gray-500 uppercase tracking-wider hover:text-black" {...props}>
      {children}
    </button>
  );
}
