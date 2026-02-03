import React, { useState, useEffect } from 'react';
import { ShoppingBag, User, Menu, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';

gsap.registerPlugin(ScrollToPlugin);

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    gsap.to(window, { duration: 1, scrollTo: `#${id}`, ease: "power2.inOut" });
    setMobileMenuOpen(false);
  };

  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-500 ${
      scrolled || mobileMenuOpen ? 'bg-daksha-black/90 backdrop-blur-md py-4' : 'bg-transparent py-6'
    }`}>
      <div className="max-w-7xl mx-auto px-6 flex justify-between items-center text-daksha-cream">
        
        {/* Desktop Nav */}
        <div className="hidden md:flex gap-8 text-sm font-light tracking-widest uppercase">
          <button onClick={() => scrollToSection('about')} className="hover:text-daksha-accent transition-colors">About</button>
          <button onClick={() => scrollToSection('collection')} className="hover:text-daksha-accent transition-colors">Collections</button>
          <button onClick={() => scrollToSection('mission')} className="hover:text-daksha-accent transition-colors">Mission</button>
          
        </div>

        {/* Logo */}
        <div className="absolute left-1/2 -translate-x-1/2 z-20">
          <Link to="/" className="font-serif text-4xl tracking-tighter hover:text-daksha-accent transition-colors">
            Daksha
          </Link>
        </div>

        {/* Right Actions */}
        <div className="flex gap-6 items-center z-20">
          <Link to="/login" className="hover:text-daksha-accent transition-colors hidden md:block">
            <User className="w-5 h-5" />
          </Link>
          <Link to="/shop" className="hover:text-daksha-accent transition-colors relative">
            <ShoppingBag className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-daksha-accent rounded-full"></span>
          </Link>
          
          {/* Mobile Menu Toggle */}
          <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="absolute top-0 left-0 w-full h-screen bg-daksha-black flex flex-col text-daksha-accent items-center justify-center gap-8 text-2xl font-serif z-10">
          <button onClick={() => scrollToSection('about')}>About</button>
          <button onClick={() => scrollToSection('collection')}>Collections</button>
          <button onClick={() => scrollToSection('mission')}>Mission</button>
          <Link to="/login" onClick={() => setMobileMenuOpen(false)}>Login</Link>
        </div>
      )}
    </nav>
  );
}