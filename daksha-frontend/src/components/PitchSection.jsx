import React, { useRef, useEffect } from "react";
import { gsap } from "gsap";

export default function PitchSection() {
  const containerRef = useRef(null);
  const textRef = useRef(null);

  useEffect(() => {
    let ctx = gsap.context(() => {
      // Desktop: Pin and Scroll Text
      gsap.matchMedia().add("(min-width: 768px)", () => {
        gsap.to(textRef.current, {
          x: () => -(textRef.current.scrollWidth - window.innerWidth),
          ease: "none",
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top top",
            end: "+=2000", // Long scroll for reading time
            pin: true,
            scrub: 1,
          }
        });
      });

      // Mobile: Simple Fade In on Scroll
      gsap.matchMedia().add("(max-width: 767px)", () => {
        gsap.from(".mobile-pitch-text", {
          opacity: 0,
          y: 50,
          stagger: 0.2,
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top 70%",
          }
        });
      });
    });
    return () => ctx.revert();
  }, []);

  return (
    <section id="mission" ref={containerRef} className="relative h-screen bg-daksha-black text-daksha-cream overflow-hidden flex items-center">
      
      {/* Desktop View */}
      <div className="hidden md:flex items-center w-full h-full overflow-hidden">
        <div ref={textRef} className="flex gap-24 px-20 whitespace-nowrap items-baseline">
          <span className="text-[8vw] font-serif font-bold">Shop Ethnic.</span>
          <span className="text-[8vw] font-serif font-bold text-daksha-accent">Shop Casual.</span>
          <span className="text-[8vw] font-serif font-bold">Shop Old Money.</span>
          <span className="text-[10vw] font-serif ml-20">Shop with <span className="text-[8vw] font-serif font-bold text-daksha-accent" >DAKSHA</span></span>
        </div>
      </div>

      {/* Mobile View */}
      <div className="md:hidden px-6 flex flex-col justify-center h-full gap-8">
        <h2 className="mobile-pitch-text text-5xl font-sans font-bold">Shop Ethnic.</h2>
        <h2 className="mobile-pitch-text text-5xl font-sans font-bold text-daksha-accent">Shop Casual.</h2>
        <h2 className="mobile-pitch-text text-6xl font-serif mt-8">Shop with DAKSHA</h2>
      </div>

    </section>
  );
}