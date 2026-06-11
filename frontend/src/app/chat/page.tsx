"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send, Sparkles, RefreshCw, User, CornerDownLeft, FileText, Bot,
  Globe,
} from "lucide-react";
import type { ChatMessage, DocumentResponse, QueryResponse } from "@/types";
import { chat, listDocuments, queryDocuments } from "@/lib/api";
import TypingIndicator from "@/components/TypingIndicator";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | undefined>(undefined);
  const [sources, setSources] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatIdRef = useRef<string>(crypto.randomUUID());

  useEffect(() => { listDocuments().then(setDocs); }, []);

  const scrollDown = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollDown(); }, [messages, loading, scrollDown]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setSources([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    setLoading(true);
    try {
      if (selectedDoc) {
        const res: QueryResponse = await queryDocuments({
          question: text,
          session_id: chatIdRef.current,
          doc_id: selectedDoc,
        });
        setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
        if (res.sources?.length) setSources(res.sources);
      } else {
        const { reply } = await chat(updated);
        setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I ran into an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  }

  function newChat() {
    setMessages([]);
    chatIdRef.current = crypto.randomUUID();
    setInput("");
    setSources([]);
  }

  const processedCount = docs.filter(d => d.processing_status === "completed").length;

  return (
    <div className="mx-auto flex h-screen max-w-4xl flex-col">
      {/* header */}
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-400" />
          <span className="text-sm font-medium">Document Chat</span>
          {selectedDoc && (
            <span className="rounded-full bg-blue-950 px-2 py-0.5 text-[10px] text-blue-400">
              {docs.find(d => d.id === selectedDoc)?.title?.slice(0, 24)}
            </span>
          )}
          {!selectedDoc && <span className="text-[10px] text-zinc-600">All documents</span>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={newChat}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200">
            <RefreshCw className="h-3.5 w-3.5" />New chat
          </button>
        </div>
      </div>

      {/* Document selector */}
      {docs.length > 0 && (
        <div className="flex items-center gap-1.5 overflow-x-auto border-b border-zinc-800/50 px-4 py-2">
          <button onClick={() => setSelectedDoc(undefined)}
            className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] transition-colors ${
              !selectedDoc ? "bg-blue-600/20 text-blue-300" : "bg-zinc-800/50 text-zinc-500 hover:text-zinc-300"
            }`}>
            <Globe className="h-3 w-3" />All
          </button>
          {docs.filter(d => d.processing_status === "completed").map(d => (
            <button key={d.id} onClick={() => setSelectedDoc(d.id)}
              className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] transition-colors ${
                selectedDoc === d.id ? "bg-blue-600/20 text-blue-300" : "bg-zinc-800/50 text-zinc-500 hover:text-zinc-300"
              }`}>
              <FileText className="h-3 w-3" />{d.title.slice(0, 20)}
            </button>
          ))}
          {docs.filter(d => d.processing_status !== "completed").length > 0 && (
            <span className="text-[10px] text-zinc-700 italic ml-1">
              +{docs.filter(d => d.processing_status !== "completed").length} processing
            </span>
          )}
        </div>
      )}

      {/* messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center px-4">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600/20">
              <Sparkles className="h-7 w-7 text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold">Ask about your documents</h2>
            <p className="mt-1 text-sm text-zinc-500">
              {processedCount > 0
                ? `${processedCount} document(s) indexed and ready for RAG queries`
                : "Upload documents first, then ask questions"}
            </p>
          </div>
        )}

        <div className="mx-auto max-w-3xl space-y-1 px-4 py-4">
          {messages.map((msg, i) => (
            <div key={i} className="group">
              {msg.role === "user" ? (
                <div className="flex justify-end gap-3 px-4 py-3">
                  <div className="max-w-[70%] rounded-2xl bg-blue-600 px-4 py-2.5 text-sm leading-relaxed text-white">{msg.content}</div>
                  <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-700">
                    <User className="h-4 w-4 text-zinc-300" />
                  </div>
                </div>
              ) : (
                <div className="flex gap-3 px-4 py-3">
                  <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600/20">
                    <Bot className="h-4 w-4 text-blue-400" />
                  </div>
                  <div className="min-w-0 pt-1.5">
                    <p className="text-sm leading-relaxed text-zinc-100 whitespace-pre-wrap">{msg.content}</p>
                    {i === messages.length - 1 && sources.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {sources.map((s, j) => (
                          <span key={j} className="rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-500">
                            {s}
                          </span>
                        ))}
                        <span className="text-[10px] text-zinc-700">(sources)</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* input */}
      <div className="border-t border-zinc-800 px-4 py-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
          <div className="relative flex items-end gap-2 rounded-2xl border border-zinc-700 bg-zinc-900/80 px-4 py-2 focus-within:border-zinc-500">
            <textarea ref={textareaRef} value={input}
              onChange={(e) => { setInput(e.target.value); autoResize(); }}
              onKeyDown={handleKeyDown}
              placeholder={selectedDoc ? "Ask about this document..." : "Ask about all documents..."}
              rows={1}
              className="max-h-[200px] flex-1 resize-none bg-transparent py-2 text-sm text-zinc-100 placeholder-zinc-500 outline-none"
            />
            <div className="flex items-center gap-1.5 pb-1">
              {input.trim() && (
                <span className="hidden text-[10px] text-zinc-600 sm:inline">
                  <CornerDownLeft className="mr-0.5 inline h-3 w-3" />Enter
                </span>
              )}
              <button type="submit" disabled={loading || !input.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-500 disabled:opacity-30">
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
          <p className="mt-2 text-center text-[10px] text-zinc-700">
            AURA retrieves relevant document context and generates grounded responses
          </p>
        </form>
      </div>
    </div>
  );
}
