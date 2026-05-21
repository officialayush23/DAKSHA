import React, { useState, useEffect, useRef } from 'react';

const AdvancedArchitectureSimulator = () => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Core Simulation State
  const [isSimulating, setIsSimulating] = useState(false);
  const [trafficVolume, setTrafficVolume] = useState(50); // 1 to 100
  const [networkQuality, setNetworkQuality] = useState(100); // 100=Fiber, 50=4G, 10=3G
  const [coalescingEnabled, setCoalescingEnabled] = useState(true);
  const [cdnOutage, setCdnOutage] = useState(false);

  // Live Telemetry State
  const [metrics, setMetrics] = useState({
    activeUsers: 0,
    fnaCacheHits: 0,
    edgeRequests: 0,
    originRequests: 0,
    droppedPackets: 0,
    originHealth: 100, // Percentage
    currentBitrate: '1080p (CMAF)'
  });

  // Canvas Engine Reference to keep values between renders without re-triggering React
  const engineRef = useRef({
    particles: [],
    lastTime: 0,
    originLoad: 0,
    tick: 0
  });

  // ---------------------------------------------------------
  // CANVAS RENDER ENGINE
  // ---------------------------------------------------------
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d', { alpha: false });
    let animationId;

    const resizeCanvas = () => {
      const rect = containerRef.current.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = 600;
    };
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Node Topology Definition
    const getTopology = (w, h) => {
      const cy = h / 2;
      return {
        users: { x: w * 0.05, y: cy, label: 'Global End Users', color: '#94a3b8', type: 'source' },
        isp: { x: w * 0.25, y: cy, label: 'L5: ISP FNA Cache', color: '#38bdf8', type: 'shield' },
        cdn1: { x: w * 0.45, y: cy - 120, label: 'L4: Akamai', color: '#f59e0b', type: 'router', online: true },
        cdn2: { x: w * 0.45, y: cy, label: 'L4: Cloudflare', color: '#f43f5e', type: 'router', online: !cdnOutage },
        cdn3: { x: w * 0.45, y: cy + 120, label: 'L4: Meta Internal', color: '#8b5cf6', type: 'router', online: true },
        edge: { x: w * 0.65, y: cy, label: 'L3: Edge PoP', color: '#c084fc', type: 'coalescer' },
        shield: { x: w * 0.80, y: cy, label: 'L3: Origin Shield', color: '#e879f9', type: 'coalescer' },
        origin: { x: w * 0.92, y: cy, label: 'L1/2: Origin', color: engineRef.current.originLoad > 80 ? '#ef4444' : '#10b981', type: 'core' }
      };
    };

    // Particle Factory
    const spawnParticle = (startX, startY, endX, endY, type, payload = {}) => {
      engineRef.current.particles.push({
        x: startX,
        y: startY,
        startX, startY, endX, endY,
        progress: 0,
        speed: (type === 'request' ? 0.015 : 0.01) * (0.8 + Math.random() * 0.4),
        type, // 'request' or 'chunk'
        color: type === 'request' ? '#38bdf8' : payload.color || '#c084fc',
        size: type === 'request' ? Math.random() * 2 + 1 : payload.size || 5,
        wobble: Math.random() * Math.PI * 2,
        stage: payload.stage || 0 // To track multi-hop journeys
      });
    };

    const drawGlowingLine = (startX, startY, endX, endY, color, isDashed, opacity) => {
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = color;
      ctx.globalAlpha = opacity;
      ctx.lineWidth = 2;
      if (isDashed) {
        ctx.setLineDash([5, 10]);
        ctx.lineDashOffset = -engineRef.current.tick * 0.5;
      } else {
        ctx.setLineDash([]);
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    };

    const renderLoop = (timestamp) => {
      if (!engineRef.current.lastTime) engineRef.current.lastTime = timestamp;
      const deltaTime = timestamp - engineRef.current.lastTime;
      engineRef.current.lastTime = timestamp;
      engineRef.current.tick++;

      const topology = getTopology(canvas.width, canvas.height);

      // 1. Draw Background
      ctx.fillStyle = '#020617'; // Deep space black/blue
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 2. Draw Network Links
      ctx.globalCompositeOperation = 'screen';
      
      // User -> ISP
      drawGlowingLine(topology.users.x, topology.users.y, topology.isp.x, topology.isp.y, '#334155', false, 0.4);
      
      // ISP -> CDNs
      ['cdn1', 'cdn2', 'cdn3'].forEach(cdn => {
        if (topology[cdn].online) {
          drawGlowingLine(topology.isp.x, topology.isp.y, topology[cdn].x, topology[cdn].y, topology[cdn].color, true, 0.3);
          drawGlowingLine(topology[cdn].x, topology[cdn].y, topology.edge.x, topology.edge.y, topology[cdn].color, true, 0.3);
        } else {
          drawGlowingLine(topology.isp.x, topology.isp.y, topology[cdn].x, topology[cdn].y, '#ef4444', false, 0.1); // Red line for outage
        }
      });

      // Edge -> Shield -> Origin
      drawGlowingLine(topology.edge.x, topology.edge.y, topology.shield.x, topology.shield.y, '#c084fc', false, 0.5);
      drawGlowingLine(topology.shield.x, topology.shield.y, topology.origin.x, topology.origin.y, engineRef.current.originLoad > 80 ? '#ef4444' : '#10b981', false, 0.5);

      // 3. System Logic & Spawning
      if (isSimulating) {
        const volumeMultiplier = trafficVolume / 50; // 0.02 to 2.0
        
        // --- INBOUND REQUESTS ---
        if (engineRef.current.tick % Math.max(1, Math.floor(5 / volumeMultiplier)) === 0) {
          // Users flood ISP
          for(let i=0; i < 5 * volumeMultiplier; i++) {
            spawnParticle(topology.users.x, topology.users.y + (Math.random() * 100 - 50), topology.isp.x, topology.isp.y, 'request', {stage: 'isp'});
            
            // Background update to metrics
            setMetrics(p => ({ ...p, activeUsers: p.activeUsers + Math.floor(Math.random() * 10) + 5 }));
          }
        }

        // --- OUTBOUND VIDEO ---
        // Video Quality logic (ABR)
        let vColor = '#a855f7'; let vSize = 6; let vLabel = '1080p';
        if (networkQuality < 70) { vColor = '#fbbf24'; vSize = 4; vLabel = '720p'; }
        if (networkQuality < 30) { vColor = '#ef4444'; vSize = 2; vLabel = '144p'; }
        
        if (engineRef.current.tick % 60 === 0 && engineRef.current.originLoad < 95) {
          setMetrics(p => ({ ...p, currentBitrate: vLabel }));
          // Origin sends chunk to Shield
          spawnParticle(topology.origin.x, topology.origin.y, topology.shield.x, topology.shield.y, 'chunk', {stage: 'shield_out', color: vColor, size: vSize});
        }
      }

      // Origin Cool Down
      if (engineRef.current.originLoad > 0) engineRef.current.originLoad -= 0.5;
      if (engineRef.current.originLoad < 0) engineRef.current.originLoad = 0;

      // 4. Update and Draw Particles
      for (let i = engineRef.current.particles.length - 1; i >= 0; i--) {
        let p = engineRef.current.particles[i];
        p.progress += p.speed * (deltaTime / 16); // Normalize speed to 60fps

        if (p.progress >= 1) {
          // Particle Reached Destination - Routing Logic
          engineRef.current.particles.splice(i, 1);

          if (isSimulating) {
            // INBOUND ROUTING
            if (p.stage === 'isp') {
              // ISP Cache hit logic (absorbs 80%)
              if (Math.random() > 0.8) {
                // Miss: Route to available CDN
                const cdns = ['cdn1', 'cdn3'];
                if (!cdnOutage) cdns.push('cdn2');
                const selectedCDN = cdns[Math.floor(Math.random() * cdns.length)];
                spawnParticle(topology.isp.x, topology.isp.y, topology[selectedCDN].x, topology[selectedCDN].y, 'request', {stage: 'cdn'});
              } else {
                if (engineRef.current.tick % 10 === 0) setMetrics(prev => ({ ...prev, fnaCacheHits: prev.fnaCacheHits + 45 }));
              }
            } 
            else if (p.stage === 'cdn') {
              spawnParticle(p.endX, p.endY, topology.edge.x, topology.edge.y, 'request', {stage: 'edge'});
            }
            else if (p.stage === 'edge') {
              if (engineRef.current.tick % 5 === 0) setMetrics(prev => ({ ...prev, edgeRequests: prev.edgeRequests + 1 }));
              
              if (coalescingEnabled) {
                // COALESCING ON: Merge requests. Only let 1 through occasionally.
                if (Math.random() > 0.95) {
                  spawnParticle(topology.edge.x, topology.edge.y, topology.shield.x, topology.shield.y, 'request', {stage: 'shield'});
                }
              } else {
                // COALESCING OFF: Thundering Herd! Pass everything.
                spawnParticle(topology.edge.x, topology.edge.y, topology.shield.x, topology.shield.y, 'request', {stage: 'shield'});
              }
            }
            else if (p.stage === 'shield') {
              if (coalescingEnabled) {
                 if (Math.random() > 0.98) spawnParticle(topology.shield.x, topology.shield.y, topology.origin.x, topology.origin.y, 'request', {stage: 'origin'});
              } else {
                 spawnParticle(topology.shield.x, topology.shield.y, topology.origin.x, topology.origin.y, 'request', {stage: 'origin'});
              }
            }
            else if (p.stage === 'origin') {
              engineRef.current.originLoad += 5; // Increase stress on origin
              
              if (engineRef.current.originLoad > 100) {
                 // ORIGIN CRASH / PACKET DROP
                 setMetrics(prev => ({ ...prev, droppedPackets: prev.droppedPackets + 1 }));
              } else {
                 setMetrics(prev => ({ ...prev, originRequests: prev.originRequests + 1 }));
              }
            }

            // OUTBOUND ROUTING (Fan out)
            else if (p.stage === 'shield_out') {
              spawnParticle(topology.shield.x, topology.shield.y, topology.edge.x, topology.edge.y, 'chunk', {stage: 'edge_out', color: p.color, size: p.size});
            }
            else if (p.stage === 'edge_out') {
              const cdns = ['cdn1', 'cdn3'];
              if (!cdnOutage) cdns.push('cdn2');
              cdns.forEach(cdn => spawnParticle(topology.edge.x, topology.edge.y, topology[cdn].x, topology[cdn].y, 'chunk', {stage: 'cdn_out', color: p.color, size: p.size}));
            }
            else if (p.stage === 'cdn_out') {
              for(let j=0; j<3; j++) spawnParticle(p.endX, p.endY, topology.isp.x, topology.isp.y, 'chunk', {stage: 'isp_out', color: p.color, size: p.size});
            }
            else if (p.stage === 'isp_out') {
              for(let j=0; j<5; j++) spawnParticle(topology.isp.x, topology.isp.y, topology.users.x, topology.users.y + (Math.random() * 200 - 100), 'chunk', {color: p.color, size: p.size});
            }
          }
        } else {
          // Draw Particle
          const curX = p.startX + (p.endX - p.startX) * p.progress;
          
          // Add sine wave wobble to requests for visual noise
          let curY = p.startY + (p.endY - p.startY) * p.progress;
          if (p.type === 'request') {
             curY += Math.sin(p.progress * Math.PI * 4 + p.wobble) * 15 * (1 - p.progress);
          }

          ctx.beginPath();
          ctx.arc(curX, curY, p.size, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.shadowBlur = p.type === 'chunk' ? 20 : 10;
          ctx.shadowColor = p.color;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }

      // Update Health Metric smoothly
      setMetrics(prev => ({
         ...prev, 
         originHealth: Math.max(0, 100 - engineRef.current.originLoad)
      }));

      // 5. Draw Nodes on top
      ctx.globalCompositeOperation = 'source-over';
      Object.values(topology).forEach(node => {
        // Outer Glow
        ctx.beginPath();
        ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = node.online === false ? 'rgba(239, 68, 68, 0.1)' : `${node.color}33`; // 33 is hex for ~20% opacity
        ctx.fill();

        // Inner Core
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = node.online === false ? '#7f1d1d' : '#0f172a';
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle = node.online === false ? '#ef4444' : node.color;
        ctx.stroke();

        // Label Background
        ctx.fillStyle = 'rgba(2, 6, 23, 0.8)';
        ctx.fillRect(node.x - 50, node.y - 45, 100, 20);

        // Label Text
        ctx.fillStyle = node.online === false ? '#ef4444' : '#e2e8f0';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(node.online === false ? 'OFFLINE' : node.label, node.x, node.y - 32);
      });

      animationId = requestAnimationFrame(renderLoop);
    };

    animationId = requestAnimationFrame(renderLoop);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [isSimulating, trafficVolume, coalescingEnabled, cdnOutage, networkQuality]);

  // ---------------------------------------------------------
  // UI RENDER
  // ---------------------------------------------------------
  return (
    <div className="w-full max-w-7xl mx-auto bg-slate-950 text-slate-200 rounded-2xl shadow-2xl overflow-hidden border border-slate-800 font-sans">
      
      {/* HEADER */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
            META-TIER STREAMING ARCHITECTURE
          </h1>
          <p className="text-slate-400 text-xs mt-1 uppercase tracking-widest font-mono">
            Interactive Global Network Telemetry Simulator
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isSimulating ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}></div>
            <span className="text-xs font-mono font-bold text-slate-300">
              {isSimulating ? 'SYSTEM LIVE' : 'STANDBY'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 grid-rows-1">
        
        {/* LEFT COLUMN - MISSION CONTROL */}
        <div className="col-span-1 border-r border-slate-800 bg-slate-900/30 p-6 flex flex-col gap-8">
          
          <button 
            onClick={() => setIsSimulating(!isSimulating)}
            className={`w-full py-4 rounded-xl font-black uppercase tracking-widest transition-all duration-300 shadow-lg ${
              isSimulating 
                ? 'bg-red-500/10 text-red-500 border border-red-500/50 hover:bg-red-500/20 shadow-red-500/20' 
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/20 shadow-emerald-500/20'
            }`}
          >
            {isSimulating ? 'Halt Simulation' : 'Engage Global Traffic'}
          </button>

          <div className="space-y-6">
            {/* Control 1: Coalescing */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-slate-300 uppercase">L3 Request Coalescing</label>
                <button 
                  onClick={() => setCoalescingEnabled(!coalescingEnabled)}
                  className={`w-12 h-6 rounded-full transition-colors relative ${coalescingEnabled ? 'bg-purple-600' : 'bg-slate-700'}`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${coalescingEnabled ? 'translate-x-7' : 'translate-x-1'}`}></div>
                </button>
              </div>
              <p className="text-[10px] text-slate-500 font-mono leading-tight">
                Disable to simulate a <span className="text-red-400">Thundering Herd</span> attack on the Origin.
              </p>
            </div>

            {/* Control 2: Traffic Volume */}
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 uppercase mb-2">
                <span>Concurrent Connections</span>
                <span className="text-blue-400 font-mono">{trafficVolume}% Load</span>
              </div>
              <input 
                type="range" min="1" max="100" value={trafficVolume} 
                onChange={(e) => setTrafficVolume(e.target.value)}
                className="w-full accent-blue-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Control 3: Multi-CDN Steering */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
               <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-slate-300 uppercase">CDN 2 Outage (BGP Drop)</label>
                <button 
                  onClick={() => setCdnOutage(!cdnOutage)}
                  className={`px-3 py-1 rounded text-xs font-bold transition-colors ${cdnOutage ? 'bg-red-500/20 text-red-500 border border-red-500' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}
                >
                  {cdnOutage ? 'RESOLVE' : 'TRIGGER'}
                </button>
              </div>
              <p className="text-[10px] text-slate-500 font-mono leading-tight">
                Simulates Cloudflare going offline. Watch the client-side intelligence instantly reroute traffic.
              </p>
            </div>

            {/* Control 4: ABR Slider */}
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 uppercase mb-2">
                <span>User Network Quality (ABR)</span>
                <span className={networkQuality > 60 ? 'text-purple-400' : networkQuality > 20 ? 'text-yellow-400' : 'text-red-400'}>
                  {metrics.currentBitrate}
                </span>
              </div>
              <input 
                type="range" min="1" max="100" value={networkQuality} 
                onChange={(e) => setNetworkQuality(e.target.value)}
                className={`w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer ${networkQuality > 60 ? 'accent-purple-500' : networkQuality > 20 ? 'accent-yellow-500' : 'accent-red-500'}`}
              />
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN - CANVAS & METRICS */}
        <div className="col-span-1 lg:col-span-3 flex flex-col relative" ref={containerRef}>
          
          {/* Top Telemetry Bar */}
          <div className="grid grid-cols-5 gap-px bg-slate-800 border-b border-slate-800">
            <MetricBox title="Global Viewers" value={metrics.activeUsers.toLocaleString()} color="text-slate-200" />
            <MetricBox title="FNA Cache Hits" value={metrics.fnaCacheHits.toLocaleString()} color="text-blue-400" />
            <MetricBox title="Edge Load" value={metrics.edgeRequests.toLocaleString()} color="text-purple-400" />
            
            {/* Critical Origin Metric */}
            <div className={`p-4 flex flex-col justify-center items-center bg-slate-900/80 transition-colors ${metrics.originHealth < 50 ? 'bg-red-950/50' : ''}`}>
              <span className="text-[10px] uppercase text-slate-500 font-bold mb-1 tracking-wider">Origin Load</span>
              <span className={`text-2xl font-black font-mono tracking-tighter ${metrics.originHealth > 80 ? 'text-emerald-400' : metrics.originHealth > 20 ? 'text-yellow-400' : 'text-red-500 animate-pulse'}`}>
                {metrics.originRequests}
              </span>
            </div>

            <MetricBox title="TCP Dropped" value={metrics.droppedPackets} color={metrics.droppedPackets > 0 ? "text-red-500" : "text-slate-600"} />
          </div>

          {/* MAIN CANVAS */}
          <div className="relative w-full h-[600px] bg-[#020617] overflow-hidden">
            
            {/* Warning Overlay */}
            {metrics.originHealth === 0 && (
              <div className="absolute inset-0 flex items-center justify-center bg-red-950/40 z-10 pointer-events-none">
                <div className="border-2 border-red-500 bg-red-950/90 p-8 rounded-2xl text-center shadow-[0_0_100px_rgba(239,68,68,0.5)]">
                  <h2 className="text-4xl font-black text-red-500 uppercase tracking-widest mb-2 animate-bounce">SYSTEM COLLAPSE</h2>
                  <p className="text-red-300 font-mono text-sm">Thundering Herd Detected. Origin Overwhelmed.</p>
                  <p className="text-red-400 font-mono text-xs mt-4 animate-pulse">Enable L3 Coalescing immediately.</p>
                </div>
              </div>
            )}

            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full"></canvas>
            
            {/* Legend */}
            <div className="absolute bottom-6 left-6 flex flex-col gap-2 bg-slate-900/80 backdrop-blur border border-slate-800 p-4 rounded-xl z-20 shadow-2xl">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Network Legend</h3>
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_10px_#38bdf8]"></span>
                <span className="text-[10px] font-mono text-slate-300">Inbound Request (Millions)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-purple-400 shadow-[0_0_10px_#c084fc]"></span>
                <span className="text-[10px] font-mono text-slate-300">CMAF Video Chunk (UDP)</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

// Helper Component for Metrics
const MetricBox = ({ title, value, color }) => (
  <div className="p-4 flex flex-col justify-center items-center bg-slate-900/80">
    <span className="text-[10px] uppercase text-slate-500 font-bold mb-1 tracking-wider">{title}</span>
    <span className={`text-2xl font-black font-mono tracking-tighter ${color}`}>{value}</span>
  </div>
);

export default AdvancedArchitectureSimulator;