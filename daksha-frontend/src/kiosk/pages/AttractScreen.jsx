import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const TAGLINE   = 'UNAPOLOGETIC ELEGANCE';

export default function AttractScreen() {
  const navigate    = useNavigate();
  const taglineRef  = useRef(null);
  const titleRef    = useRef(null);
  const [ready, setReady] = useState(false);

  // ── Letter-scramble entrance (same algorithm as Hero.jsx) ──────────────────
  useEffect(() => {
    // Brief delay so the page has painted before animation starts
    const startDelay = setTimeout(() => {
      setReady(true);

      let iterations = 0;
      const interval = setInterval(() => {
        if (!taglineRef.current) return;
        taglineRef.current.innerText = TAGLINE
          .split('')
          .map((letter, index) => {
            if (index < iterations) return TAGLINE[index];
            if (letter === ' ') return ' ';
            return ALPHABET[Math.floor(Math.random() * 26)];
          })
          .join('');

        if (iterations >= TAGLINE.length) clearInterval(interval);
        iterations += 1 / 2;
      }, 40);

      return () => clearInterval(interval);
    }, 400);

    return () => clearTimeout(startDelay);
  }, []);

  return (
    <div className="h-screen w-full relative overflow-hidden bg-black select-none">

      {/* Video background — same Coverr fashion video as landing page Hero */}
      <div className="absolute inset-0 opacity-60">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover"
        >
          <source
            src="https://cdn.coverr.co/videos/coverr-fashion-model-posing-in-neon-lights-5674/1080p.mp4"
            type="video/mp4"
          />
        </video>
        {/* Dark overlay — identical to landing Hero */}
        <div className="absolute inset-0 bg-black/40" />
      </div>

      {/* Main content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">

        {/* DAKSHA wordmark — same serif / mix-blend treatment as Hero */}
        <h1
          ref={titleRef}
          className="text-[18vw] md:text-[14vw] font-serif leading-[0.85] tracking-tighter text-white mix-blend-difference"
          style={{
            opacity: ready ? 1 : 0,
            transform: ready ? 'translateY(0)' : 'translateY(60px)',
            transition: 'opacity 1.2s cubic-bezier(0.16,1,0.3,1), transform 1.2s cubic-bezier(0.16,1,0.3,1)',
          }}
        >
          DAKSHA
        </h1>

        {/* Scrambling tagline */}
        <p
          ref={taglineRef}
          className="mt-4 text-xs md:text-lg tracking-[0.5em] font-sans uppercase font-light text-white/80"
          style={{
            opacity: ready ? 1 : 0,
            transition: 'opacity 0.8s ease 0.6s',
            minWidth: '20ch',
          }}
        >
          LOADING...
        </p>

        {/* CTA — replaces the landing page's "Scroll" indicator */}
        <div
          className="mt-16"
          style={{
            opacity: ready ? 1 : 0,
            transform: ready ? 'translateY(0)' : 'translateY(20px)',
            transition: 'opacity 1s ease 1s, transform 1s cubic-bezier(0.16,1,0.3,1) 1s',
          }}
        >
          <button
            type="button"
            onClick={() => navigate('/kiosk/login')}
            className="group flex items-center gap-4 text-lg md:text-xl tracking-widest uppercase text-white border-b-2 border-white pb-2 hover:text-zinc-300 hover:border-zinc-300 transition-all duration-300 bg-transparent cursor-pointer"
          >
            Begin Your Journey
            <ArrowRight
              className="group-hover:translate-x-2 transition-transform duration-300"
              size={22}
            />
          </button>
        </div>
      </div>

      {/* Version badge */}
      <div className="absolute bottom-8 w-full text-center text-white/30 text-xs tracking-widest uppercase">
        Daksha Kiosk · v1.0
      </div>
    </div>
  );
}
