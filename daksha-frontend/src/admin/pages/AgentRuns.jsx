import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Bot, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function AgentRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    AdminService.listAgentRuns()
      .then(res => setRuns(Array.isArray(res) ? res : res.data || []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Agent Runs</h1>
        <p className="text-muted-foreground">Monitor automated system decisions</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Execution Log</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Trigger Event</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Executed At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? <TableRow><TableCell colSpan={5} className="text-center h-24"><Loader2 className="animate-spin mx-auto"/></TableCell></TableRow> : 
                runs.map(run => (
                <TableRow key={run.id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Bot className="h-4 w-4 text-blue-500" />
                    {run.agent_name || "Unknown"}
                    <span className="text-xs text-muted-foreground ml-2">({run.agent_role})</span>
                  </TableCell>
                  <TableCell>{run.trigger_event}</TableCell>
                  <TableCell>
                    <Badge variant={run.status === 'completed' ? 'default' : 'destructive'}>{run.status}</Badge>
                  </TableCell>
                  <TableCell>{run.confidence ? `${(run.confidence * 100).toFixed(0)}%` : 'N/A'}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{format(new Date(run.started_at), 'MMM dd, yyyy HH:mm')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}