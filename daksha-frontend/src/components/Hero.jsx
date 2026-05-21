import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
gsap.registerPlugin(ScrollTrigger);

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

export default function Hero() {
  const titleRef = useRef(null);
  const taglineRef = useRef(null);

  useEffect(() => {
    // 1. Jumble Text Animation
    const originalText = "UNAPOLOGETIC ELEGANCE"; // Modern confident tagline
    let iterations = 0;
    
    const interval = setInterval(() => {
      if (!taglineRef.current) return;
      taglineRef.current.innerText = originalText
        .split("")
        .map((letter, index) => {
          if (index < iterations) return originalText[index];
          if (letter === " ") return " ";
          return ALPHABET[Math.floor(Math.random() * 26)];
        })
        .join("");

      if (iterations >= originalText.length) clearInterval(interval);
      iterations += 1 / 2;
    }, 40);

    // 2. Reveal Animations
    const tl = gsap.timeline();
    tl.fromTo(titleRef.current, 
      { y: 100, opacity: 0 }, 
      { y: 0, opacity: 1, duration: 1.5, ease: "power4.out", delay: 0.5 }
    );

    return () => clearInterval(interval);
  }, []);

  // Scroll-based reveal: title scale + video parallax
  const videoRef = useRef(null);
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Parallax: video drifts up as user scrolls
      if (videoRef.current) {
        gsap.to(videoRef.current, {
          yPercent: -20,
          ease: "none",
          scrollTrigger: {
            trigger: "section",
            start: "top top",
            end: "bottom top",
            scrub: true,
          },
        });
      }
      // Title scale-down on scroll
      if (titleRef.current) {
        gsap.to(titleRef.current, {
          scale: 0.85,
          opacity: 0.6,
          ease: "none",
          scrollTrigger: {
            trigger: "section",
            start: "top top",
            end: "40% top",
            scrub: 1,
          },
        });
      }
    });
    return () => ctx.revert();
  }, []);

  return (
    <section className="relative h-screen w-full overflow-hidden bg-daksha-black text-daksha-cream">
      {/* Video Background */}
      <div className="absolute inset-0 opacity-60">
        <video 
          autoPlay loop muted playsInline 
          ref={videoRef}
          className="w-full h-full object-cover"
        >
          {/* Use a real fashion video URL here */}
          <source src="https://cdn.coverr.co/videos/coverr-fashion-model-posing-in-neon-lights-5674/1080p.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/40" /> {/* Overlay */}
      </div>

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4">
        <h1 ref={titleRef} className="text-[15vw] md:text-[12vw] font-serif leading-[0.8] tracking-tighter mix-blend-difference">
          DAKSHA
        </h1>
        <p ref={taglineRef} className="mt-6 text-sm md:text-xl tracking-[0.5em] font-sans uppercase font-light">
          LOADING...
        </p>
      </div>
      
      {/* Scroll Indicator */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-70 animate-bounce">
        <span className="text-[10px] tracking-widest uppercase">Scroll</span>
        <div className="w-[1px] h-12 bg-white"></div>
      </div>
    </section>
  );
}