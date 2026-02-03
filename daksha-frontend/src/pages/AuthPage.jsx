import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { toast } from 'sonner';
import { User, Lock, Mail, Phone } from 'lucide-react';
import api from '../lib/api';

export default function AuthPage({ isRegister = false }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let result;
      if (isRegister) {
        result = await supabase.auth.signUp({ email, password });
        if (result.error) throw result.error;
        
        // Sync with Backend
        await api.post('/user/register', { email, name });
        toast.success("Account created! Check your email.");
      } else {
        result = await supabase.auth.signInWithPassword({ email, password });
        if (result.error) throw result.error;
        toast.success("Welcome back to Daksha");
        navigate('/shop');
      }
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-daksha-cream">
      <div className="w-full max-w-md bg-white p-8 md:p-12 shadow-2xl border border-gray-100">
        <h1 className="text-4xl font-serif text-center mb-2">
          {isRegister ? "Join Daksha" : "Welcome Back"}
        </h1>
        <p className="text-center text-gray-400 text-xs tracking-widest uppercase mb-8">
          {isRegister ? "Begin your journey" : "Access your collection"}
        </p>

        <form onSubmit={handleAuth} className="space-y-6">
          {isRegister && (
            <div className="relative">
              <User className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
              <input 
                type="text" placeholder="Full Name" 
                className="w-full pl-10 p-3 border-b border-gray-200 focus:border-daksha-black outline-none transition-colors font-sans"
                value={name} onChange={e => setName(e.target.value)}
                required
              />
            </div>
          )}
          
          <div className="relative">
            <Mail className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
            <input 
              type="email" placeholder="Email Address" 
              className="w-full pl-10 p-3 border-b border-gray-200 focus:border-daksha-black outline-none transition-colors font-sans"
              value={email} onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
            <input 
              type="password" placeholder="Password" 
              className="w-full pl-10 p-3 border-b border-gray-200 focus:border-daksha-black outline-none transition-colors font-sans"
              value={password} onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <button 
            disabled={loading}
            className="w-full bg-daksha-black text-white py-4 mt-4 uppercase tracking-widest text-sm hover:bg-daksha-accent transition-colors disabled:opacity-50"
          >
            {loading ? "Processing..." : (isRegister ? "Create Account" : "Sign In")}
          </button>
        </form>

        <div className="mt-6 text-center">
          <a href={isRegister ? "/login" : "/register"} className="text-sm text-gray-500 hover:text-black border-b border-transparent hover:border-black transition-all">
            {isRegister ? "Already a member? Login" : "New to Daksha? Register"}
          </a>
        </div>
      </div>
    </div>
  );
}