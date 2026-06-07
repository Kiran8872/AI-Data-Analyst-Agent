/* eslint-disable */
"use client";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Send, Bot, User as UserIcon, PlusCircle, MessageSquare, FileSpreadsheet, HardDrive, Clock, Trash2, Download } from "lucide-react";
import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

type Dataset = {
  id: number;
  filename: string;
  size_bytes: number;
  created_at: string;
};

type Session = {
  session_id: string;
  dataset_ids: string;
  title: string;
  created_at: string;
};

type Message = {
  role: "user" | "ai";
  content: string;
};

export default function ChatPage() {
  const { token } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
  
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const showError = (msg: string) => {
    setError(msg);
    setTimeout(() => setError(null), 5000);
  };

  useEffect(() => {
    fetchDatasets();
    fetchSessionsGlobal();
  }, [token]);

  const fetchDatasets = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/datasets/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
        if (data.length > 0) setSelectedDatasetIds([data[0].id]);
      } else {
        showError("Failed to fetch datasets. Server returned " + res.status);
      }
    } catch (e) {
      console.error(e);
      showError("Failed to connect to the server. Please check your connection.");
    }
  };

  const fetchSessionsGlobal = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && selectedSessionId === null && messages.length === 0) {
          setSelectedSessionId(data[data.length - 1].session_id);
        }
      } else {
        showError("Failed to load chat sessions.");
      }
    } catch (e) {
      console.error(e);
      showError("Network error while loading sessions.");
    }
  };

  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  const confirmDeleteSession = async () => {
    if (!token || !sessionToDelete) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat/sessions/${sessionToDelete}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        if (selectedSessionId === sessionToDelete) {
          setSelectedSessionId(null);
          setMessages([]);
        }
        fetchSessionsGlobal();
      } else {
        showError("Failed to delete chat session.");
      }
    } catch (err) {
      console.error(err);
      showError("Network error while deleting session.");
    } finally {
      setSessionToDelete(null);
    }
  };

  useEffect(() => {
    const fetchChatHistory = async () => {
      if (!token || !selectedSessionId) return;
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat/history/${selectedSessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const history = await res.json();
          setMessages(history.map((m: any) => ({ role: m.role, content: m.content })));
        } else {
          showError("Failed to fetch chat history.");
        }
      } catch (e) {
        console.warn("Failed to fetch chat history", e);
        showError("Network error while loading chat history.");
      }
    };
    if (selectedSessionId) {
      fetchChatHistory();
    } else {
      setMessages([]);
    }
  }, [selectedSessionId, token]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || selectedDatasetIds.length === 0 || !token) return;

    const userMessage = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat/`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
          dataset_ids: selectedDatasetIds, 
          question: userMessage,
          session_id: selectedSessionId
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { role: "ai", content: data.answer }]);
        if (!selectedSessionId) {
          setSelectedSessionId(data.session_id);
          fetchSessionsGlobal();
        }
      } else {
        const errorData = await res.json().catch(() => ({}));
        const errorMessage = errorData.detail || `Server error (${res.status}).`;
        setMessages(prev => [...prev, { role: "ai", content: `**Error:** ${errorMessage}` }]);
      }
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "ai", content: `**Network Error:** ${e.message || "Failed to connect to the server."}` }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleDataset = (id: number) => {
    setSelectedDatasetIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const exportPDF = async () => {
    try {
      const element = document.getElementById('chat-messages-container');
      if (!element) return;
      const html2pdf = (await import('html2pdf.js')).default;
      const opt: any = {
        margin:       0.5,
        filename:     `Analysis-Report-${new Date().getTime()}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      html2pdf().set(opt).from(element).save();
    } catch (error) {
      console.error("Failed to export PDF:", error);
      alert("Failed to export PDF. Please try again or check your browser console.");
    }
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-6 animate-in fade-in duration-500">
      
      {/* Left Pane - Sessions & Datasets */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-4">
        <div className="flex flex-col gap-2">
           <h2 className="text-sm font-bold tracking-wider text-slate-900 dark:text-slate-100 uppercase">Context Datasets</h2>
           <div className="border rounded-lg bg-card shadow-sm w-full p-2 max-h-48 overflow-y-auto space-y-2">
             {datasets.length > 0 ? datasets.map(ds => (
               <label key={ds.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 p-1 rounded">
                 <input 
                   type="checkbox" 
                   checked={selectedDatasetIds.includes(ds.id)} 
                   onChange={() => toggleDataset(ds.id)} 
                   className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                 />
                 <span className="truncate">{ds.filename}</span>
               </label>
             )) : (
               <div className="text-xs text-muted-foreground text-center py-2">No datasets available</div>
             )}
           </div>
        </div>
        
        <div className="flex items-center justify-between mt-2">
           <h2 className="text-xs font-bold tracking-wider text-muted-foreground uppercase">Recent Chats</h2>
           <Button variant="ghost" size="icon" className="h-6 w-6 text-indigo-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/50" onClick={() => {setSelectedSessionId(null); setMessages([]);}}>
             <PlusCircle className="h-4 w-4" />
           </Button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1.5 pr-2">
           <Button 
             variant={selectedSessionId === null ? "default" : "outline"} 
             className={`w-full justify-start shadow-sm transition-all ${selectedSessionId === null ? 'bg-indigo-600 hover:bg-indigo-700 text-white border-transparent' : 'border-dashed'}`}
             onClick={() => {setSelectedSessionId(null); setMessages([]);}}
           >
              <PlusCircle className="mr-2 h-4 w-4" /> New Chat
           </Button>
           {sessions.map(s => (
             <div key={s.session_id} className={`flex items-center group w-full rounded-md transition-all ${selectedSessionId === s.session_id ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' : 'text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
               <Button 
                 variant="ghost" 
                 className="flex-1 justify-start text-left truncate text-xs shadow-none bg-transparent hover:bg-transparent"
                 onClick={() => setSelectedSessionId(s.session_id)}
               >
                 <MessageSquare className="mr-2 h-3.5 w-3.5 shrink-0" /> 
                 <span className="truncate">{s.title}</span>
               </Button>
               <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-500" onClick={(e) => { e.stopPropagation(); setSessionToDelete(s.session_id); }}>
                 <Trash2 className="h-3.5 w-3.5" />
               </Button>
             </div>
           ))}
        </div>
      </div>

      {/* Middle Pane - Chat Interface */}
      <Card className="flex-1 flex flex-col overflow-hidden shadow-lg border-slate-200 dark:border-slate-800 bg-card/50 backdrop-blur-sm relative">
        {error && (
          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded-lg shadow-md flex items-center gap-2 animate-in slide-in-from-top-4 fade-in duration-300">
             <span className="text-sm font-medium">{error}</span>
             <Button variant="ghost" size="icon" className="h-4 w-4 ml-2 hover:bg-red-200 hover:text-red-900 rounded-full" onClick={() => setError(null)}>
               &times;
             </Button>
          </div>
        )}
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={exportPDF} className="absolute top-4 right-4 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur shadow-sm hover:bg-indigo-50 hover:text-indigo-600">
            <Download className="h-4 w-4 mr-2" /> Export PDF
          </Button>
        )}
        <CardContent className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" id="chat-messages-container">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground animate-in zoom-in duration-500">
              <div className="bg-indigo-500/10 p-4 rounded-full mb-4">
                <Bot className="h-10 w-10 text-indigo-500 opacity-80" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">Start a New Analysis</h3>
              <p className="max-w-xs mt-2 text-sm">Select multiple datasets and ask questions. The AI will cross-reference data and generate interactive charts.</p>
              <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-md">
                <span className="px-3 py-1.5 bg-muted rounded-full text-xs cursor-pointer hover:bg-indigo-50 hover:text-indigo-600 transition-colors" onClick={() => setInput("What are the key statistics?")}>"What are the key statistics?"</span>
                <span className="px-3 py-1.5 bg-muted rounded-full text-xs cursor-pointer hover:bg-indigo-50 hover:text-indigo-600 transition-colors" onClick={() => setInput("Plot an interactive chart")}>"Plot an interactive chart"</span>
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3.5 ${m.role === 'user' ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-3 duration-300`}>
              <div className={`p-2 rounded-full h-9 w-9 flex items-center justify-center shrink-0 shadow-sm ${m.role === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' : 'bg-slate-100 dark:bg-slate-800 border'}`}>
                {m.role === 'user' ? <UserIcon className="h-5 w-5" /> : <Bot className="h-5 w-5 text-indigo-500" />}
              </div>
              <div className={`p-4 rounded-2xl shadow-sm max-w-[85%] overflow-x-auto ${m.role === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-tr-sm' : 'bg-card border border-slate-100 dark:border-slate-800 rounded-tl-sm w-full'}`}>
                <div className={`prose prose-sm max-w-none w-full ${m.role === 'user' ? 'prose-invert' : 'dark:prose-invert prose-indigo'}`}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code: (props: any) => {
                        const match = /language-(\w+)/.exec(props.className || '');
                        if (!props.inline && match && match[1] === 'plotly') {
                          try {
                            const data = JSON.parse(String(props.children).replace(/\n$/, ''));
                            return (
                              <div className="w-full h-[400px] border rounded-lg overflow-hidden bg-white mt-4 p-2">
                                <Plot 
                                  data={data.data || data} 
                                  layout={{...(data.layout || {}), autosize: true, margin: {l:40, r:20, t:40, b:40}}} 
                                  useResizeHandler={true} 
                                  style={{width: '100%', height: '100%'}} 
                                />
                              </div>
                            );
                          } catch (e) {
                            return <div className="text-red-500 p-2 border border-red-200 rounded">Error rendering interactive chart. Invalid JSON data.</div>;
                          }
                        }
                        return <code className={props.className} {...props}>{props.children}</code>;
                      },
                      img: (props: any) => {
                        const src = typeof props.src === 'string' && props.src.startsWith('/') ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${props.src}` : props.src;
                        return <img {...props} src={src} className="rounded-lg border shadow-sm max-w-full h-auto mt-3" alt={props.alt || "Chart"} />;
                      }
                    }}
                  >
                    {m.content}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {loading && (
             <div className="flex gap-3.5 animate-in fade-in slide-in-from-bottom-2">
              <div className="p-2 rounded-full h-9 w-9 flex items-center justify-center shrink-0 bg-slate-100 dark:bg-slate-800 border"><Bot className="h-5 w-5 text-indigo-500" /></div>
              <div className="p-4 rounded-2xl rounded-tl-sm bg-card border shadow-sm max-w-[80%] flex items-center gap-3">
                <div className="flex gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce"></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "150ms" }}></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "300ms" }}></div>
                </div>
                <span className="text-sm text-muted-foreground font-medium">Agent is analyzing...</span>
              </div>
            </div>
          )}
        </CardContent>
        <div className="p-4 bg-card/80 backdrop-blur border-t" data-html2canvas-ignore="true">
          <form onSubmit={handleSend} className="flex gap-3 relative">
            <Input 
              placeholder={selectedDatasetIds.length > 0 ? "Ask your data a question..." : "Select a dataset first..."} 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading || selectedDatasetIds.length === 0}
              className="py-6 pl-4 pr-12 rounded-xl shadow-inner bg-muted/50 border-transparent focus-visible:ring-indigo-500"
            />
            <Button type="submit" size="icon" disabled={loading || selectedDatasetIds.length === 0 || !input.trim()} className="absolute right-2 top-2 h-8 w-8 rounded-lg bg-indigo-600 hover:bg-indigo-700 transition-all">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
      
      <Dialog open={sessionToDelete !== null} onOpenChange={(open) => !open && setSessionToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Chat Session?</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this chat history? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSessionToDelete(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDeleteSession}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
