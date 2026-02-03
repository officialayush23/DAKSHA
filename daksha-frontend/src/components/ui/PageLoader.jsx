import React, { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';

const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

export default function PageLoader({ isLoading }) {
  const textRef = useRef(null);
  const [progress, setProgress] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    if (isLoading) {
      // 1. Reset
      setProgress(0);
      gsap.set(containerRef.current, { yPercent: 0 });

      // 2. Fake Progress Logic
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 99) {
            clearInterval(progressInterval);
            return 99;
          }
          return prev + Math.floor(Math.random() * 10) + 1;
        });
      }, 150);

      // 3. Jumble Text Logic
      let iterations = 0;
      const text = "DAKSHA";
      const jumbleInterval = setInterval(() => {
        if (textRef.current) {
          textRef.current.innerText = text
            .split("")
            .map((letter, index) => {
              if (index < iterations) return text[index];
              return CHARS[Math.floor(Math.random() * 26)];
            })
            .join("");
        }
        if (iterations >= text.length) clearInterval(jumbleInterval);
        iterations += 1 / 3;
      }, 50);

      return () => {
        clearInterval(progressInterval);
        clearInterval(jumbleInterval);
      };
    } else {
      // Exit Animation (Curtain Up)
      setProgress(100);
      gsap.to(containerRef.current, {
        yPercent: -100,
        duration: 0.8,
        ease: "power4.inOut",
        delay: 0.2
      });
    }
  }, [isLoading]);

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-[100] bg-daksha-black text-daksha-cream flex flex-col items-center justify-center"
    >
      <h1 ref={textRef} className="text-9xl font-serif tracking-tighter">DAKSHA</h1>
      <div className="mt-8 flex flex-col items-center gap-2">
        <span className="font-sans text-xs tracking-[0.3em]">{progress}%</span>
        <div className="w-64 h-[1px] bg-white/20">
          <div 
            className="h-full bg-daksha-accent transition-all duration-300 ease-out" 
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}