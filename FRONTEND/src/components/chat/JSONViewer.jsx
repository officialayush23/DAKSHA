// src/components/chat/JSONViewer.jsx

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Code } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";

export default function JSONViewer({ data, title = "Payload" }) {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!data) return null;
  
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-2">
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors">
        {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        <Code className="h-3 w-3" />
        <span>{title}</span>
        <Badge variant="outline" className="text-[10px] px-1.5 py-0">
          {typeof data === 'object' ? 'JSON' : 'Text'}
        </Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="text-xs bg-muted/50 p-3 rounded-md overflow-auto max-h-64 font-mono border border-border/40 mt-2">
          {JSON.stringify(data, null, 2)}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}
