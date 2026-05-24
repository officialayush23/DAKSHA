import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { KioskService } from '@/lib/kioskApi';
import { useKiosk } from '../context/KioskSessionContext';
import { Button } from "@/components/ui/button";
import { ArrowRight, Delete, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const NUMPAD = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '⌫', '0', '✓'];

export default function LoginScreen() {
  const { kioskId, setUser, setSessionId, resetIdleTimer } = useKiosk();
  const navigate = useNavigate();
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = useCallback(async (currentPhone) => {
    const digits = currentPhone ?? phone;
    if (digits.length !== 10) {
      toast.error("Please enter a valid 10-digit number");
      return;
    }
    setLoading(true);
    try {
      const res = await KioskService.login(digits, kioskId);
      if (res?.user_id) {
        setUser({
          id: res.user_id,
          name: res.name,
          phone: res.phone,
          store_id: res.store_id,
        });
        if (res.session_id && typeof setSessionId === 'function') {
          setSessionId(res.session_id);
        }
        toast.success(`Welcome back, ${res.name || 'User'}!`);
        navigate('/kiosk/chat');
      } else {
        toast.error("Phone number not found. Please register via the app first.");
      }
    } catch {
      toast.error("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [phone, kioskId, setUser, setSessionId, navigate]);

  const handleNumpad = (val) => {
    if (loading) return;
    resetIdleTimer();
    if (val === '⌫') {
      setPhone(prev => prev.slice(0, -1));
    } else if (val === '✓') {
      handleLogin();
    } else {
      setPhone(prev => prev.length < 10 ? prev + val : prev);
    }
  };

  // Physical keyboard support — uses a ref-based approach to avoid stale closures
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (loading) return;
      resetIdleTimer();
      if (e.key >= '0' && e.key <= '9') {
        setPhone(prev => prev.length < 10 ? prev + e.key : prev);
      } else if (e.key === 'Backspace') {
        e.preventDefault();
        setPhone(prev => prev.slice(0, -1));
      } else if (e.key === 'Enter') {
        // Read phone via functional update so the value is always fresh
        setPhone(prev => {
          if (prev.length === 10) handleLogin(prev);
          return prev;
        });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [loading, resetIdleTimer, handleLogin]);

  const handleSkip = () => {
    toast.info("Browsing as Guest");
    navigate('/kiosk/shop');
  };

  const formattedPhone = phone
    ? phone.slice(0, 5) + (phone.length > 5 ? ' ' + phone.slice(5) : '')
    : '';

  return (
    <div className="h-full w-full flex flex-col md:flex-row bg-white">

      {/* Left: Instructions */}
      <div className="flex-1 p-12 flex flex-col justify-center space-y-8 bg-slate-50 border-r">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight text-slate-900">
            Enter Your<br />Phone Number
          </h1>
          <p className="text-2xl text-slate-500 max-w-md leading-relaxed">
            Login with your <span className="font-semibold text-primary">Daksha</span> registered number to access your profile.
          </p>
        </div>

        <div className="space-y-6">
          {[
            "Enter your registered phone number",
            "Access your profile & loyalty points",
            "Sync your mobile cart & wishlist",
          ].map((step, i) => (
            <div key={i} className="flex items-center gap-4 text-xl text-slate-700">
              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold shrink-0">
                {i + 1}
              </div>
              <span>{step}</span>
            </div>
          ))}
        </div>

        <div className="pt-8">
          <Button
            type="button"
            variant="ghost"
            size="lg"
            onClick={handleSkip}
            className="text-xl h-16 px-8 text-slate-500 hover:text-primary"
          >
            Skip for now <ArrowRight className="ml-2 w-6 h-6" />
          </Button>
        </div>
      </div>

      {/* Right: Numpad */}
      <div className="flex-1 p-12 flex flex-col items-center justify-center bg-white gap-8">

        {/* Phone Display */}
        <div className="w-full max-w-sm">
          <div className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-3 text-center">
            Mobile Number
          </div>
          <div className={`
            h-24 w-full rounded-2xl border-2 flex items-center justify-center text-4xl font-bold tracking-widest transition-all
            ${phone.length === 10
              ? 'border-green-400 bg-green-50 text-green-800'
              : 'border-slate-200 bg-slate-50 text-slate-900'}
          `}>
            {formattedPhone || (
              <span className="text-slate-300 text-3xl">_ _ _ _ _ _ _ _ _ _</span>
            )}
          </div>
        </div>

        {/* Numpad Grid — all buttons are type="button" to prevent any form submission */}
        <div className="grid grid-cols-3 gap-4 w-full max-w-sm">
          {NUMPAD.map((key) => {
            const isConfirm = key === '✓';
            const isDelete  = key === '⌫';
            return (
              <button
                key={key}
                type="button"
                onClick={() => handleNumpad(key)}
                disabled={loading}
                className={`
                  h-20 rounded-2xl text-2xl font-bold flex items-center justify-center
                  transition-all duration-150 active:scale-95 select-none
                  ${isConfirm
                    ? 'bg-green-600 text-white hover:bg-green-700 shadow-lg shadow-green-200'
                    : isDelete
                      ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      : 'bg-slate-50 text-slate-900 border border-slate-200 hover:bg-slate-100 hover:border-slate-300 shadow-sm'
                  }
                  ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                {loading && isConfirm ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : isDelete ? (
                  <Delete className="w-6 h-6" />
                ) : (
                  key
                )}
              </button>
            );
          })}
        </div>

        {/* Login Button */}
        <Button
          type="button"
          size="lg"
          className="w-full max-w-sm h-16 text-xl rounded-2xl shadow-xl"
          onClick={() => handleLogin()}
          disabled={phone.length !== 10 || loading}
        >
          {loading ? (
            <><Loader2 className="mr-3 h-6 w-6 animate-spin" /> Logging in...</>
          ) : (
            'Login'
          )}
        </Button>
      </div>
    </div>
  );
}
