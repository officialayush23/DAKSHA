import React from 'react';
import { Link } from 'react-router-dom';

export default function ErrorPage() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-daksha-black text-daksha-cream text-center px-6">
      <h1 className="text-[10vw] font-serif leading-none opacity-20 select-none">500</h1>
      <h2 className="text-3xl font-display mb-4">OOP's</h2>
      <p className="text-gray-400 max-w-md mb-8">
        Looks like DAKSHA is having a moment. Our AI agents are fixing the threads.
      </p>
      <Link to="/" className="border border-white px-8 py-3 uppercase tracking-widest hover:bg-white hover:text-black transition-colors">
        Return Home
      </Link>
    </div>
  );
}