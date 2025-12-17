//  FRONTEND/src/components/product/ReviewSection.jsx

import { useState } from "react";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import api from "@/lib/apiClient";
import { toast } from "sonner";

export default function ReviewSection({ productId, reviews }) {
  const [rating, setRating] = useState(0);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  async function submitReview() {
    if (!rating) return toast.error("Select a rating");

    setLoading(true);
    try {
      await api.post("/feedback/submit", {
        product_id: productId,
        rating,
        review_text: text,
      });
      toast.success("Review submitted");
      setText("");
      setRating(0);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 mt-10">
      <h3 className="text-lg font-semibold">Reviews</h3>

      {/* ADD REVIEW */}
      <div className="p-4 rounded-xl bg-card border">
        <div className="flex gap-1 mb-2">
          {[1,2,3,4,5].map(i => (
            <Star
              key={i}
              className={`h-5 w-5 cursor-pointer ${
                i <= rating ? "fill-primary text-primary" : "text-muted-foreground"
              }`}
              onClick={() => setRating(i)}
            />
          ))}
        </div>

        <Textarea
          placeholder="Write your review…"
          value={text}
          onChange={e => setText(e.target.value)}
        />

        <Button
          className="mt-3"
          onClick={submitReview}
          disabled={loading}
        >
          Submit Review
        </Button>
      </div>

      {/* LIST */}
      <div className="space-y-4">
        {reviews.items.map((r, i) => (
          <div key={i} className="p-4 rounded-xl bg-card border">
            <div className="flex gap-1 mb-1">
              {[...Array(r.rating)].map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-primary text-primary" />
              ))}
            </div>
            <p className="text-sm text-muted-foreground">
              {r.review_text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
