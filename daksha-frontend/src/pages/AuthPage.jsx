import React, { useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { SessionService } from "../lib/api";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { User, Lock, Mail, Phone, MapPin } from "lucide-react";

export default function AuthPage({ isRegister = false }) {
  const navigate = useNavigate();

  const [email, setEmail]               = useState("");
  const [password, setPassword]         = useState("");
  const [name, setName]                 = useState("");
  const [phone, setPhone]               = useState("");
  const [loading, setLoading]           = useState(false);
  const [locationAllowed, setLocationAllowed] = useState(false);
  const [awaitingVerification, setAwaitingVerification] = useState(false);

  const requestLocation = () => {
    if (!("geolocation" in navigator)) { toast.error("Geolocation not supported"); return; }
    navigator.geolocation.getCurrentPosition(
      () => { setLocationAllowed(true); toast.success("Location permission granted"); },
      () => { toast.warning("Location denied. Pickup may be limited."); }
    );
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isRegister) {
        // ── Sign Up ──────────────────────────────────────────────────────
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { name, phone } },
        });
        if (error) throw error;

        if (!data.session) {
          // Email confirmation is ON — user must verify before logging in.
          // The backend user row will be auto-created on first authenticated request.
          setAwaitingVerification(true);
          toast.success("Account created! Check your email to verify.");
          setLoading(false);
          return;
        }

        // Email confirmation OFF (local / Supabase project with it disabled) —
        // session is immediately available, start the backend session now.
        await SessionService.start("web");
        toast.success("Account created! Welcome.");
        navigate("/dash/shop");

      } else {
        // ── Sign In ──────────────────────────────────────────────────────
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;

        await SessionService.start("web");
        toast.success("Welcome back");
        navigate("/dash/shop");
      }
    } catch (err) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  // ── Email verification waiting screen ───────────────────────────────────────
  if (awaitingVerification) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFDFD]">
        <div className="w-full max-w-md p-8 text-center">
          <h1 className="text-5xl font-serif mb-6 tracking-tighter">Daksha</h1>
          <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="text-white w-7 h-7" />
          </div>
          <h2 className="text-xl font-serif mb-3">Check your email</h2>
          <p className="text-sm text-gray-500 mb-8">
            We sent a verification link to <strong>{email}</strong>.<br />
            Click it to activate your account, then sign in.
          </p>
          <button
            onClick={() => { setAwaitingVerification(false); navigate("/login"); }}
            className="w-full bg-black text-white py-4 uppercase text-xs tracking-[0.2em]"
          >
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  // ── Main form ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FDFDFD]">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-serif mb-2 tracking-tighter">Daksha</h1>
          <p className="text-xs uppercase tracking-[0.3em] text-gray-400">
            {isRegister ? "Begin your journey" : "Member Access"}
          </p>
        </div>

        <form onSubmit={handleAuth} className="space-y-6">
          {isRegister && (
            <>
              <div className="relative">
                <User className="absolute left-0 top-3 text-gray-300 w-5 h-5" />
                <input required value={name} onChange={e => setName(e.target.value)}
                  placeholder="Full Name"
                  className="w-full pl-8 border-b py-3 outline-none font-serif" />
              </div>
              <div className="relative">
                <Phone className="absolute left-0 top-3 text-gray-300 w-5 h-5" />
                <input required value={phone} onChange={e => setPhone(e.target.value)}
                  placeholder="Phone (for concierge)"
                  className="w-full pl-8 border-b py-3 outline-none font-serif" />
              </div>
            </>
          )}

          <div className="relative">
            <Mail className="absolute left-0 top-3 text-gray-300 w-5 h-5" />
            <input required type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="Email"
              className="w-full pl-8 border-b py-3 outline-none font-serif" />
          </div>

          <div className="relative">
            <Lock className="absolute left-0 top-3 text-gray-300 w-5 h-5" />
            <input required type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full pl-8 border-b py-3 outline-none font-serif" />
          </div>

          <button type="button" onClick={requestLocation}
            className={`w-full flex items-center justify-center gap-2 py-3 border rounded-full text-xs uppercase tracking-widest ${
              locationAllowed ? "border-emerald-500 text-emerald-600" : "border-gray-300 text-gray-500"
            }`}>
            <MapPin size={14} />
            {locationAllowed ? "Location Enabled" : "Enable Location (Optional)"}
          </button>

          <button disabled={loading}
            className="w-full bg-black text-white py-4 uppercase text-xs tracking-[0.2em] mt-8 disabled:opacity-50">
            {loading ? "Processing..." : isRegister ? "Create Account" : "Enter"}
          </button>
        </form>

        <div className="mt-8 text-center">
          <a href={isRegister ? "/login" : "/register"}
            className="text-xs text-gray-400 uppercase tracking-wider">
            {isRegister ? "Already a member? Sign in" : "New here? Register"}
          </a>
        </div>
      </div>
    </div>
  );
}
