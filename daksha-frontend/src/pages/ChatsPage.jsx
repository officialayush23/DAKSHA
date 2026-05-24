// src/pages/ChatsPage.jsx — Chat history / tickets page
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBasePath } from '../hooks/useBasePath';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Plus, Clock, ChevronRight, Loader2 } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

function timeAgo(iso) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ChatsPage() {
  const navigate = useNavigate();
  const { basePath } = useBasePath();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const res = await api.get('/chat/sessions');
      setSessions(res.data || []);
    } catch {
      toast.error('Failed to load chat history');
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = async () => {
    setCreating(true);
    try {
      const res = await api.post('/chat/sessions/new');
      const { session_id } = res.data;
      navigate(`${basePath}/agent`, { state: { sessionId: session_id } });
    } catch {
      toast.error('Failed to start new chat');
    } finally {
      setCreating(false);
    }
  };

  const continueChat = (sessionId) => {
    navigate(`${basePath}/agent`, { state: { sessionId } });
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-serif tracking-tight">Conversations</h1>
          <p className="text-xs text-gray-400 uppercase tracking-widest mt-1">Your chat history</p>
        </div>
        <button
          onClick={startNewChat}
          disabled={creating}
          className="flex items-center gap-2 bg-black text-white px-5 py-2.5 text-xs uppercase tracking-widest hover:bg-gray-900 transition-colors disabled:opacity-50"
        >
          {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          New Chat
        </button>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="animate-spin text-gray-300" size={32} />
        </div>
      ) : sessions.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="text-center py-20"
        >
          <MessageSquare size={48} className="mx-auto text-gray-200 mb-4" />
          <p className="text-gray-400 font-serif text-lg">No conversations yet</p>
          <p className="text-xs text-gray-300 mt-2 uppercase tracking-wider">Start a chat with your concierge</p>
          <button
            onClick={startNewChat}
            className="mt-6 bg-black text-white px-6 py-3 text-xs uppercase tracking-widest"
          >
            Begin
          </button>
        </motion.div>
      ) : (
        <AnimatePresence>
          <div className="space-y-2">
            {sessions.map((s, i) => (
              <motion.div
                key={s.session_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => continueChat(s.session_id)}
                className="group flex items-center justify-between p-4 border border-gray-100 hover:border-black transition-all cursor-pointer bg-white hover:bg-gray-50"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center flex-shrink-0">
                    <MessageSquare size={14} className="text-white" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">
                      {s.name || <span className="text-gray-400 italic">Untitled conversation</span>}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400 uppercase tracking-wider">{s.channel}</span>
                      <span className="text-gray-200">·</span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock size={10} />
                        {timeAgo(s.last_message_at || s.updated_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <ChevronRight size={16} className="text-gray-300 group-hover:text-black transition-colors flex-shrink-0" />
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  );
}
