import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const IMAGES = [
  "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&q=80",
  "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80",
  "https://images.unsplash.com/photo-1617137968427-85924c800a22?w=800&q=80",
  "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=800&q=80",
  "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&q=80",
  "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&q=80"
];

// Reusable Image Card
const ProductCard = ({ src }) => (
  <div className="w-full aspect-[3/4] bg-gray-200 relative group">
    <img 
      src={src} 
      alt="Product" 
      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
    />
    <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity" />
  </div>
);

export default function ProductMarquee() {
  const sectionRef = useRef(null);
  const columnsRef = useRef([]);

  useEffect(() => {
    let ctx = gsap.context(() => {
      // DESKTOP ANIMATION: Parallax Columns
      gsap.matchMedia().add("(min-width: 768px)", () => {
        // Pin the section
        ScrollTrigger.create({
          trigger: sectionRef.current,
          start: "top top",
          end: "+=2000",
          pin: true,
          scrub: 1,
        });

        // Move columns up/down
        columnsRef.current.forEach((col, i) => {
          const direction = i % 2 === 0 ? -1 : 1; // Alternate direction
          gsap.to(col, {
            y: direction * 500, // Move 500px up or down
            ease: "none",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top top",
              end: "+=2000",
              scrub: 1,
            },
          });
        });

        // Title Fade
        gsap.to(".collection-title", {
          opacity: 0,
          scale: 1.5,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top top",
            end: "+=500",
            scrub: true
          }
        });
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section id="collection" ref={sectionRef} className="relative min-h-screen bg-daksha-black overflow-hidden flex flex-col md:block">
      
      {/* Title Overlay */}
      <div className="collection-title absolute inset-0 z-20 flex flex-col items-center justify-center pointer-events-none mix-blend-difference px-4 text-center">
        <p className="text-daksha-cream text-sm tracking-[0.5em] mb-4">DISCOVER</p>
        <h2 className="text-daksha-cream text-6xl md:text-9xl font-serif">The <span className="text-daksha-accent">DAKSHA</span> Collection</h2>
      </div>

      {/* DESKTOP: Parallax Columns */}
      <div className="hidden md:flex justify-center gap-6 w-full h-[120vh] -mt-[10vh] opacity-60">
        {[0, 1, 2, 3].map((colIndex) => (
          <div 
            key={colIndex} 
            ref={el => columnsRef.current[colIndex] = el}
            className={`flex flex-col gap-6 w-1/4 ${colIndex % 2 === 0 ? '-mt-40' : 'mt-0'}`}
          >
            {[...IMAGES, ...IMAGES].map((src, i) => (
              <ProductCard key={i} src={src} />
            ))}
          </div>
        ))}
      </div>

      {/* MOBILE: Horizontal Scroll (Simple Marquee) */}
      <div className="md:hidden flex items-center h-screen overflow-x-auto no-scrollbar snap-x snap-mandatory">
        <div className="flex gap-4 px-4 w-max animate-scroll-left">
          {[...IMAGES, ...IMAGES, ...IMAGES].map((src, i) => (
            <div key={i} className="w-[70vw] snap-center shrink-0">
              <ProductCard src={src} />
            </div>
          ))}
        </div>
      </div>

      {/* Gradient Mask (Desktop Only) */}
      <div className="hidden md:block absolute bottom-0 left-0 w-full h-40 bg-gradient-to-t from-daksha-black to-transparent z-10" />
    </section>
  );
}