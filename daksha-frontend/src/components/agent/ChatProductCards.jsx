// src/components/agent/ChatProductCards.jsx
// Product results inside the concierge chat.
//  - the whole card opens the product page (on the exact colour/size shown)
//  - "Add" adds that exact variant, shows a toast with a "View bag" action,
//    and refreshes the bag badge
//  - exact matches and alternatives are labelled differently; image matches
//    say why they matched
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, Plus, Check } from "lucide-react";
import api from "../../lib/api";

const PLACEHOLDER = "https://placehold.co/400x500/F4F4F5/a1a1aa?text=Daksha";

const logOutcome = (impressionId, outcome_type, reward_value) => {
  if (!impressionId) return;
  api.post("/recommendations/outcome", { impression_id: impressionId, outcome_type, reward_value }).catch(() => {});
};

const BADGES = {
  related: { text: "Alternative", cls: "bg-amber-50 text-amber-700 border-amber-200" },
  "other-colour": { text: "Other colour", cls: "bg-amber-50 text-amber-700 border-amber-200" },
  visual: { text: "Visual match", cls: "bg-sky-50 text-sky-700 border-sky-200" },
};

function ProductCard({ p, basePath }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [state, setState] = useState("idle"); // idle | adding | added

  const open = () => {
    logOutcome(p.impression_id, "click", 0.1);
    const pid = p.product_id || p.variant_id;
    navigate(`${basePath}/product/${pid}${p.variant_id ? `?variant=${p.variant_id}` : ""}`);
  };

  const add = async (e) => {
    e.stopPropagation();
    if (!p.variant_id) {
      toast.error("This item can't be added right now.");
      return;
    }
    if (state === "adding") return;
    setState("adding");
    logOutcome(p.impression_id, "cart", 0.5);
    try {
      await api.post("/cart/quick-add", { variant_id: p.variant_id, quantity: 1 });
      setState("added");
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      toast.success(`${p.name} added to your bag`, {
        description: [p.color, p.size].filter(Boolean).join(" · ") || undefined,
        action: { label: "View bag", onClick: () => navigate(`${basePath}/cart`) },
      });
      setTimeout(() => setState("idle"), 2500);
    } catch (err) {
      setState("idle");
      const detail = err?.response?.data?.detail;
      toast.error("Couldn't add to bag", {
        description: typeof detail === "string" ? detail : "Please try again in a moment.",
      });
    }
  };

  const badge = BADGES[p.match];
  const price = p.final_price ?? p.price ?? p.base_price ?? 0;
  const hasOffer = p.base_price && p.final_price && p.final_price < p.base_price;

  return (
    <div
      role="link"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } }}
      aria-label={`${p.name}${p.color ? `, ${p.color}` : ""}, ₹${price}. Open details`}
      className="group snap-start shrink-0 w-[180px] sm:w-[200px] rounded-2xl border border-zinc-200 bg-white overflow-hidden shadow-sm hover:shadow-md hover:border-zinc-300 transition-all cursor-pointer text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-black"
    >
      <div className="relative h-44 w-full bg-zinc-100 overflow-hidden">
        <img
          src={p.image || p.image_url || PLACEHOLDER}
          alt=""
          loading="lazy"
          onError={(e) => { e.currentTarget.src = PLACEHOLDER; }}
          className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-300"
        />
        {badge && (
          <span className={`absolute top-2 left-2 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badge.cls}`}>
            {badge.text}
          </span>
        )}
      </div>
      <div className="p-3 space-y-1">
        {p.brand && <p className="text-[10px] uppercase tracking-widest text-zinc-400">{p.brand}</p>}
        <p className="font-semibold text-sm leading-tight line-clamp-2 text-zinc-900">{p.name}</p>
        {(p.color || p.size) && (
          <p className="text-xs text-zinc-500">{[p.color, p.size].filter(Boolean).join(" · ")}</p>
        )}
        {p.why && <p className="text-[11px] text-sky-700">{p.why}</p>}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-semibold text-black">₹{Number(price).toLocaleString("en-IN")}</span>
            {hasOffer && (
              <span className="text-[11px] text-zinc-400 line-through">₹{Number(p.base_price).toLocaleString("en-IN")}</span>
            )}
          </div>
          <button
            type="button"
            onClick={add}
            disabled={state === "adding"}
            aria-label={`Add ${p.name} to bag`}
            className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
              state === "added" ? "bg-emerald-600 text-white" : "bg-black text-white hover:bg-zinc-800"
            } disabled:opacity-60`}
          >
            {state === "adding" ? <Loader2 size={13} className="animate-spin" />
              : state === "added" ? <Check size={13} /> : <Plus size={13} />}
            {state === "added" ? "Added" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ChatProductCards({ products, meta, basePath }) {
  if (!products?.length) return null;
  const exact = products.filter((p) => !["related", "other-colour"].includes(p.match));
  const alts = products.length - exact.length;
  return (
    <div className="w-full max-w-[320px] sm:max-w-[460px] md:max-w-[640px]">
      {meta?.query && (
        <p className="text-[11px] uppercase tracking-wider text-zinc-400 mb-1">
          {meta.mode === "image" ? meta.query : `Showing ${meta.query}`}
          {alts > 0 && exact.length > 0 && ` · ${exact.length} exact, ${alts} alternative${alts > 1 ? "s" : ""}`}
          {alts > 0 && exact.length === 0 && " · no exact matches, alternatives below"}
        </p>
      )}
      <div className="flex overflow-x-auto gap-3 pb-3 pt-1 snap-x scrollbar-hide">
        {products.map((p, idx) => (
          <ProductCard key={`${p.variant_id || idx}`} p={p} basePath={basePath} />
        ))}
      </div>
    </div>
  );
}
