import { BrowserRouter } from 'react-router-dom';
import React, { useEffect } from 'react';
import Lenis from 'lenis';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import ProductMarquee from '../components/ProductMarquee';
import PitchSection from '../components/PitchSection';
import Testimonials from '../components/Testimonials';
import FAQ from '../components/FAQ';
import Footer from '../components/Footer';
import { ArrowRight } from 'lucide-react';

export default function LandingPage() {
  useEffect(() => {
    // Initialize Smooth Scroll
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smooth: true,
    });

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }, []);

  return (
    <div className="font-sans antialiased bg-daksha-cream">
      <Navbar />
      
      <main>
        <Hero />
        <ProductMarquee />
        <PitchSection />
        <Testimonials />
        
        {/* CTA Section */}
        <section className="h-[70vh] flex flex-col items-center justify-center bg-white text-center px-6 border-t border-gray-100">
          <h2 className="text-5xl md:text-8xl font-serif mb-10">What are you waiting for?</h2>
          <a href="/dash" className="group flex items-center gap-4 text-xl md:text-2xl tracking-widest uppercase border-b-2 border-black pb-2 hover:text-daksha-accent hover:border-daksha-accent transition-all">
            Enter the Shop
            <ArrowRight className="group-hover:translate-x-2 transition-transform" />
          </a>
        </section>

        <FAQ />
      </main>

      <Footer />
    </div>
  );
}