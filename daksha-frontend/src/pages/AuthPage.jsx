// src/pages/AuthPage.jsx
import React, { useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { AuthService, UserService } from '../lib/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Mail, Phone } from 'lucide-react';

export default function AuthPage({ isRegister = false }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // --- Live Location Logic ---
  const syncLocation = async () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          // You might need a dedicated endpoint for this, or update address later
          // For now, let's assume we log it or send it to a /session/location endpoint
          console.log("📍 Location captured:", latitude, longitude);
        } catch (e) {
          console.error("Location sync failed", e);
        }
      });
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isRegister) {
        // 1. Supabase Sign Up
        const { error: authError } = await supabase.auth.signUp({
          email, password, options: { data: { name, phone } }
        });
        if (authError) throw authError;

        // 2. Sync to Backend with Phone
        await AuthService.syncUser({ name, phone });

        // 3. Sync Location
        syncLocation();

        toast.success("Welcome to the Inner Circle.");
        navigate('/dash/shop');
      } else {
        // Login
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        
        syncLocation();
        toast.success("Welcome back.");
        navigate('/dash/shop');
      }
    } catch (err) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

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
              <div className="relative group">
                <User className="absolute left-0 top-3 text-gray-300 w-5 h-5 group-focus-within:text-black transition-colors" />
                <input 
                  type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)}
                  className="w-full pl-8 border-b border-gray-200 py-3 outline-none focus:border-black transition-colors bg-transparent placeholder:text-gray-300 font-serif"
                  required
                />
              </div>
              <div className="relative group">
                <Phone className="absolute left-0 top-3 text-gray-300 w-5 h-5 group-focus-within:text-black transition-colors" />
                <input 
                  type="tel" placeholder="Phone Number (for Concierge)" value={phone} onChange={e => setPhone(e.target.value)}
                  className="w-full pl-8 border-b border-gray-200 py-3 outline-none focus:border-black transition-colors bg-transparent placeholder:text-gray-300 font-serif"
                  required
                />
              </div>
            </>
          )}
          
          <div className="relative group">
            <Mail className="absolute left-0 top-3 text-gray-300 w-5 h-5 group-focus-within:text-black transition-colors" />
            <input 
              type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full pl-8 border-b border-gray-200 py-3 outline-none focus:border-black transition-colors bg-transparent placeholder:text-gray-300 font-serif"
              required
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-0 top-3 text-gray-300 w-5 h-5 group-focus-within:text-black transition-colors" />
            <input 
              type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full pl-8 border-b border-gray-200 py-3 outline-none focus:border-black transition-colors bg-transparent placeholder:text-gray-300 font-serif"
              required
            />
          </div>
          
          <button disabled={loading} className="w-full bg-black text-white py-4 uppercase text-xs font-bold tracking-[0.2em] hover:bg-zinc-800 transition-all disabled:opacity-50 mt-8">
            {loading ? 'Processing...' : (isRegister ? 'Create Account' : 'Enter')}
          </button>
        </form>
        
        <div className="mt-8 text-center">
          <a href={isRegister ? "/login" : "/register"} className="text-xs text-gray-400 hover:text-black transition-colors border-b border-transparent hover:border-black pb-1 uppercase tracking-wider">
            {isRegister ? "Already a member? Sign In" : "New here? Register"}
          </a>
        </div>
      </div>
    </div>
  );
}