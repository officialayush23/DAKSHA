import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { KioskService } from '@/lib/kioskApi';
import { useKiosk } from '../context/KioskSessionContext';
import { Button } from "@/components/ui/button";
import { Loader2, ScanLine, ArrowRight, RefreshCcw } from 'lucide-react';
import { toast } from 'sonner';
import { KIOSK_CONFIG } from '../constants';

export default function LoginScreen() {
  const { kioskId, setUser, endSession } = useKiosk();
  const navigate = useNavigate();
  const [qrValue, setQrValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // New error state
  const pollingInterval = useRef(null);

  // 1. Generate QR Code
  useEffect(() => {
    let mounted = true;
    initSession(mounted);
    return () => {
      mounted = false;
      stopPolling();
    };
  }, [kioskId]);

  const initSession = async (mounted) => {
    try {
      setLoading(true);
      setError(null);
      console.log(`📡 Requesting QR for Kiosk ID: ${kioskId}`);

      // API Call
      const response = await KioskService.generateKioskQr(kioskId);
      console.log("✅ Backend Response:", response);

      if (mounted) {
        // Handle different response formats (String vs JSON)
        let qrString = '';
        if (typeof response === 'string') {
          qrString = response;
        } else if (response?.url) {
          qrString = response.url;
        } else if (response?.qr_code) {
          qrString = response.qr_code;
        } else {
          // Fallback: verify if the response itself is the data
          qrString = JSON.stringify(response); 
        }

        if (qrString) {
          setQrValue(qrString);
          startPolling();
        } else {
          throw new Error("Empty QR data received");
        }
      }
    } catch (err) {
      console.error("❌ QR Generation Failed:", err);
      if (mounted) {
        setError(err.message || "Connection Failed");
        toast.error("Could not connect to Kiosk Server");
      }
    } finally {
      if (mounted) setLoading(false);
    }
  };

  // 2. Poll for Status
  const startPolling = () => {
    stopPolling();
    pollingInterval.current = setInterval(checkStatus, KIOSK_CONFIG.POLLING_INTERVAL_MS);
  };

  const stopPolling = () => {
    if (pollingInterval.current) clearInterval(pollingInterval.current);
  };

  const checkStatus = async () => {
    try {
      const sessionData = await KioskService.checkSessionStatus();
      if (sessionData && sessionData.user) {
        stopPolling();
        setUser(sessionData.user);
        toast.success(`Welcome, ${sessionData.user.name || 'User'}!`);
        navigate('/kiosk/catalog');
      }
    } catch (error) {
      // Ignore errors while waiting
    }
  };

  const handleRetry = () => {
    initSession(true);
  };

  const handleSkipLogin = () => {
    stopPolling();
    toast.info("Browsing as Guest");
    navigate('/kiosk/catalog');
  };

  return (
    <div className="h-full w-full flex flex-col md:flex-row bg-white">
      {/* Left: Instructions */}
      <div className="flex-1 p-12 flex flex-col justify-center space-y-8 bg-slate-50 border-r">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight text-slate-900">Scan to Login</h1>
          <p className="text-2xl text-slate-500 max-w-md leading-relaxed">
            Open the <span className="font-semibold text-primary">Daksha App</span> on your phone and scan the code.
          </p>
        </div>
        
        {/* Steps */}
        <div className="space-y-6">
          <div className="flex items-center gap-4 text-xl text-slate-700">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">1</div>
            <span>Access your Profile</span>
          </div>
          <div className="flex items-center gap-4 text-xl text-slate-700">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">2</div>
            <span>Sync Mobile Cart</span>
          </div>
        </div>

        <div className="pt-8">
          <Button variant="ghost" size="lg" onClick={handleSkipLogin} className="text-xl h-16 px-8 text-slate-500 hover:text-primary">
            Skip for now <ArrowRight className="ml-2 w-6 h-6" />
          </Button>
        </div>
      </div>

      {/* Right: QR Code */}
      <div className="flex-1 p-12 flex items-center justify-center bg-white relative">
        <div className="text-center space-y-6">
          <div className="bg-white p-6 rounded-3xl shadow-xl border-2 border-slate-100 inline-block relative min-h-[300px] min-w-[300px] flex items-center justify-center">
            {loading ? (
              <Loader2 className="w-12 h-12 text-slate-300 animate-spin" />
            ) : error ? (
              <div className="flex flex-col items-center gap-4">
                <p className="text-red-500 font-medium">{error}</p>
                <Button variant="outline" onClick={handleRetry} className="gap-2">
                  <RefreshCw className="w-4 h-4" /> Retry
                </Button>
              </div>
            ) : qrValue ? (
              <>
                <QRCodeSVG value={qrValue} size={300} level="H" includeMargin={true} />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
                  <ScanLine className="w-64 h-64 text-primary animate-pulse" />
                </div>
              </>
            ) : null}
          </div>
          
          <p className="text-slate-400 text-lg animate-pulse">
            {loading ? "Generating secure code..." : error ? "Connection failed" : "Waiting for scan..."}
          </p>
        </div>

        <Button variant="ghost" className="absolute top-8 right-8 text-slate-400" onClick={() => endSession()}>
          Cancel Session
        </Button>
      </div>
    </div>
  );
}