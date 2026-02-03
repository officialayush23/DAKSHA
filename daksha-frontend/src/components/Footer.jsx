import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-daksha-black text-daksha-cream py-20 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
        
        <div className="space-y-6">
          <h1 className="text-[12vw] md:text-[8vw] font-serif leading-none">DAKSHA</h1>
          <p className="text-gray-400 max-w-sm">
            Redefining the modern wardrobe with AI-driven precision and timeless aesthetics.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-16 text-sm tracking-widest uppercase">
          <div className="space-y-4 flex flex-col">
            <span className="text-daksha-accent font-bold mb-2">Explore</span>
            <a href="#" className="hover:text-white transition-colors">Shop</a>
            <a href="#" className="hover:text-white transition-colors">Collections</a>
            <a href="#" className="hover:text-white transition-colors">About</a>
          </div>
          <div className="space-y-4 flex flex-col">
            <span className="text-daksha-accent font-bold mb-2">Legal</span>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">FAQ</a>
          </div>
        </div>
      </div>
      
      <div className="border-t border-white/10 mt-20 pt-8 flex justify-between text-xs text-gray-500">
        <p>© 2026 DAKSHA RETAIL AI. All Rights Reserved.</p>
        <p>Made with Elegance</p>
      </div>
    </footer>
  );
}