import React, { useEffect } from 'react';
import { gsap } from 'gsap';

const TestimonialCard = ({ text, author, className }) => (
  <div className={`testimonial-card bg-white p-8 w-80 md:w-96 shadow-2xl border border-gray-100 flex flex-col justify-between h-64 hover:scale-105 transition-transform duration-300 ${className}`}>
    <p className="font-serif text-2xl leading-relaxed">"{text}"</p>
    <div className="flex items-center gap-4 mt-6">
      <div className="w-10 h-10 bg-daksha-black rounded-full" />
      <span className="text-xs font-bold uppercase tracking-widest">{author}</span>
    </div>
  </div>
);

export default function Testimonials() {
  useEffect(() => {
    // Floating Animation (Desktop Only)
    const ctx = gsap.matchMedia();
    ctx.add("(min-width: 768px)", () => {
      gsap.utils.toArray(".testimonial-card").forEach((card, i) => {
        gsap.to(card, {
          y: i % 2 === 0 ? -20 : 20,
          duration: 2 + i,
          yoyo: true,
          repeat: -1,
          ease: "sine.inOut"
        });
      });
    });
    return () => ctx.revert();
  }, []);

  return (
    <section id="about" className="py-24 bg-daksha-cream overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-20 text-center">
        <h2 className="text-4xl md:text-8xl font-serif mb-4">Voices of Elegance</h2>
        <p className="text-gray-500 uppercase mt-1 tracking-widest text-sm">Trusted by 50,000+ Users</p>
      </div>

      <div className="flex flex-col md:flex-row justify-center items-center gap-10 md:gap-16 px-4 md:h-[500px]">
        <TestimonialCard 
          text="The fabric breathes confidence. I've never felt more powerful." 
          author="Rohan M." 
          className="md:-rotate-3 md:mt-20"
        />
        <TestimonialCard 
          text="Finally, a brand that understands the subtle art of Indian luxury." 
          author="Priya S." 
          className="md:rotate-12 md:-mt-10 z-10"
        />
        <TestimonialCard 
          text="The AI suggestions knew my style better than I did." 
          author="Arjun K." 
          className="md:-rotate-x-6 md:mt-32"
        />
      </div>
    </section>
  );
}