import React, { useState } from 'react';
import { Plus, Minus } from 'lucide-react';

const FAQS = [
  { q: "How does the AI sizing work?", a: "We use a 3D body mapping algorithm based on your height and weight inputs." },
  { q: "What is your return policy?", a: "30-day no-questions-asked returns on all unworn items." },
  { q: "Do you ship internationally?", a: "Yes, we ship to over 100 countries via DHL Express." },
  { q: "Are the fabrics sustainable?", a: "100% of our cotton is organic and sourced from ethical farms in India." }
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <section className="py-24 bg-daksha-black text-daksha-cream px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-sm font-bold uppercase tracking-widest mb-16 text-gray-500">Common Questions</h2>
        
        <div className="space-y-4">
          {FAQS.map((faq, i) => (
            <div 
              key={i} 
              className="border-b border-gray-800 pb-8 cursor-pointer group"
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              onMouseEnter={() => setOpenIndex(i)} // Desktop Hover
            >
              <div className="flex justify-between items-center py-4">
                <h3 className={`text-2xl md:text-4xl font-serif transition-colors duration-300 ${openIndex === i ? 'text-daksha-accent' : 'text-daksha-cream'}`}>
                  {faq.q}
                </h3>
                <div className="text-daksha-accent">
                  {openIndex === i ? <Minus /> : <Plus />}
                </div>
              </div>
              
              <div className={`overflow-hidden transition-all duration-500 ease-in-out ${openIndex === i ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}`}>
                <p className="text-lg md:text-xl text-gray-400 font-sans max-w-3xl">
                  {faq.a}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}