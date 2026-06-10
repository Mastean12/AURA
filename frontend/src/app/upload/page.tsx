"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Upload, File, FileText, FileSpreadsheet, FileImage, X, CheckCircle,
  AlertCircle, Loader2, Trash2, Download, Search, ChevronDown,
  FileX, FolderOpen, RefreshCw,
} from "lucide-react";
import { uploadFileWithProgress, listDocuments, deleteDocument } from "@/lib/api";
import type { UploadResponse, DocumentResponse } from "@/types";

const ALLOWED = ".csv,.docx,.pdf,.xlsx";

type UploadState =
  | { phase: "idle" }
  | { phase: "selected"; file: File }
  | { phase: "uploading"; file: File; progress: number }
  | { phase: "success"; file: File; result: UploadResponse }
  | { phase: "error"; file: File; message: string };

const TYPE_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  PDF: { label: "PDF Documents", icon: FileText, color: "text-red-400", bg: "bg-red-600/10" },
  Word: { label: "Word Documents", icon: File, color: "text-blue-400", bg: "bg-blue-600/10" },
  Excel: { label: "Excel Data", icon: FileSpreadsheet, color: "text-emerald-400", bg: "bg-emerald-600/10" },
  Other: { label: "Other Files", icon: FileImage, color: "text-zinc-400", bg: "bg-zinc-600/10" },
};

function formatSize(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  return `${(bytes / 1_000).toFixed(1)} KB`;
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function UploadPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [batchDeleting, setBatchDeleting] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>({ phase: "idle" });
  const [dragOver, setDragOver] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const inputRef = useState<HTMLInputElement | null>(null);
  const fileInputRef = useCallback((el: HTMLInputElement | null) => { inputRef[1](el); }, []);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try { setDocs(await listDocuments()); } catch { setDocs([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs, refreshKey]);

  const selectFile = useCallback((f: File) => {
    setUploadState({ phase: "selected", file: f });
  }, []);

  const startUpload = useCallback(async () => {
    if (uploadState.phase !== "selected") return;
    const file = uploadState.file;
    setUploadState({ phase: "uploading", file, progress: 0 });
    try {
      const result = await uploadFileWithProgress(file, (pct) => {
        setUploadState({ phase: "uploading", file, progress: pct });
      });
      setUploadState({ phase: "success", file, result });
      setTimeout(() => setRefreshKey(k => k + 1), 500);
    } catch (e) {
      setUploadState({ phase: "error", file, message: (e as Error).message });
    }
  }, [uploadState]);

  const resetUpload = useCallback(() => {
    setUploadState({ phase: "idle" });
  }, []);

  async function handleDelete(docId: number) {
    try {
      await deleteDocument(docId);
      setDocs(prev => prev.filter(d => d.id !== docId));
      setSelectedIds(prev => { const n = new Set(prev); n.delete(docId); return n; });
      setDeleteConfirm(null);
    } catch { /* ignore */ }
  }

  async function handleBatchDelete() {
    setBatchDeleting(true);
    const ids = Array.from(selectedIds);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/documents/batch-delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_ids: ids }),
      });
      if (res.ok) {
        setDocs(prev => prev.filter(d => !selectedIds.has(d.id)));
        setSelectedIds(new Set());
      }
    } catch { /* ignore */ }
    finally { setBatchDeleting(false); }
  }

  function toggleSelect(id: number) {
    setSelectedIds(prev => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  }

  const grouped = docs.reduce<Record<string, DocumentResponse[]>>((acc, doc) => {
    const t = doc.file_type || "Other";
    if (!acc[t]) acc[t] = [];
    acc[t].push(doc);
    return acc;
  }, {});

  const typeOrder = ["PDF", "Word", "Excel", "Other"];

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Document Manager</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Upload, organize, and manage your documents. Supported: PDF, DOCX, CSV, XLSX
          </p>
        </div>
        <button onClick={() => setRefreshKey(k => k + 1)}
          className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Upload Zone */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) selectFile(f); }}
          onClick={uploadState.phase === "idle" ? () => document.getElementById("file-input")?.click() : undefined}
          className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
            dragOver ? "border-blue-400 bg-blue-950/30" : "border-zinc-700 hover:border-zinc-500"
          }`}
        >
          <input id="file-input" ref={fileInputRef} type="file" accept={ALLOWED} className="hidden"
            onChange={(e) => e.target.files?.[0] && selectFile(e.target.files[0])} />

          {uploadState.phase === "idle" && (
            <>
              <Upload className="mb-3 h-8 w-8 text-zinc-500" />
              <p className="text-sm font-medium text-zinc-300">Drop files here or click to browse</p>
              <p className="mt-1 text-xs text-zinc-600">PDF &bull; DOCX &bull; CSV &bull; XLSX</p>
            </>
          )}
        </div>

        {/* File Selected / Uploading / Error */}
        {(uploadState.phase === "selected" || uploadState.phase === "uploading" || uploadState.phase === "error") && (
          <div className={`mt-4 flex items-center justify-between rounded-xl border px-4 py-3 ${
            uploadState.phase === "error" ? "border-red-800 bg-red-950/20" : "border-zinc-800 bg-zinc-900/70"
          }`}>
            <div className="flex items-center gap-3 min-w-0">
              <File className="h-5 w-5 shrink-0 text-blue-400" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{uploadState.file.name}</p>
                <p className="text-xs text-zinc-500">{(uploadState.file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {uploadState.phase === "selected" && (
                <>
                  <button onClick={startUpload} className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium hover:bg-blue-500">Upload</button>
                  <button onClick={resetUpload} className="rounded-lg p-1.5 text-zinc-500 hover:text-zinc-300"><X className="h-4 w-4" /></button>
                </>
              )}
              {uploadState.phase === "uploading" && (
                <span className="flex items-center gap-1.5 text-sm text-zinc-400"><Loader2 className="h-4 w-4 animate-spin" />{uploadState.progress}%</span>
              )}
              {uploadState.phase === "error" && (
                <>
                  <span className="flex items-center gap-1 text-sm text-red-400"><AlertCircle className="h-4 w-4" />{uploadState.message}</span>
                  <button onClick={resetUpload} className="rounded-lg p-1.5 text-zinc-500 hover:text-zinc-300"><X className="h-4 w-4" /></button>
                </>
              )}
            </div>
          </div>
        )}

        {uploadState.phase === "uploading" && (
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
            <div className="h-full rounded-full bg-blue-500 transition-all duration-300" style={{ width: `${uploadState.progress}%` }} />
          </div>
        )}

        {uploadState.phase === "success" && (
          <div className="mt-4 flex items-center gap-3 rounded-xl border border-emerald-800 bg-emerald-950/20 px-4 py-3">
            <CheckCircle className="h-5 w-5 shrink-0 text-emerald-400" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-300">{uploadState.result.filename} uploaded successfully</p>
              <p className="text-xs text-zinc-500">{(uploadState.result.size / 1024).toFixed(1)} KB</p>
            </div>
            <button onClick={resetUpload} className="text-xs text-zinc-500 underline underline-offset-2 hover:text-zinc-300">Upload another</button>
          </div>
        )}
      </div>

      {/* Document Library */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold tracking-tight">Document Library</h2>
            <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400">{docs.length} file{docs.length !== 1 ? "s" : ""}</span>
          </div>
          {selectedIds.size > 0 && (
            <button onClick={handleBatchDelete} disabled={batchDeleting}
              className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium hover:bg-red-500 disabled:opacity-50">
              {batchDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
              Delete {selectedIds.size} selected
            </button>
          )}
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <div key={i} className="h-20 animate-pulse rounded-xl bg-zinc-800/50" />)}
          </div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-800 py-16">
            <FolderOpen className="mb-3 h-10 w-10 text-zinc-700" />
            <p className="text-sm text-zinc-600">No documents uploaded yet</p>
            <p className="text-xs text-zinc-700 mt-1">Upload files above to get started</p>
          </div>
        ) : (
          <div className="space-y-6">
            {typeOrder.map(type => {
              const items = grouped[type] || [];
              if (items.length === 0) return null;
              const cfg = TYPE_CONFIG[type] || TYPE_CONFIG.Other;
              const Icon = cfg.icon;
              return (
                <div key={type}>
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`h-4 w-4 ${cfg.color}`} />
                    <h3 className={`text-xs font-medium uppercase tracking-wider ${cfg.color}`}>{cfg.label}</h3>
                    <span className="text-xs text-zinc-600">({items.length})</span>
                  </div>
                  <div className="space-y-1">
                    {items.map(doc => {
                      const isSelected = selectedIds.has(doc.id);
                      const isConfirming = deleteConfirm === doc.id;
                      return (
                        <div key={doc.id}
                          className={`group flex items-center gap-3 rounded-xl border px-4 py-3 transition-colors ${
                            isSelected ? "border-blue-600/50 bg-blue-600/10" : "border-zinc-800 bg-zinc-900/30 hover:bg-zinc-900/60"
                          }`}>
                          {/* Checkbox */}
                          <button onClick={() => toggleSelect(doc.id)}
                            className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                              isSelected ? "border-blue-500 bg-blue-500" : "border-zinc-700 hover:border-zinc-500"
                            }`}>
                            {isSelected && <span className="text-[10px] font-bold text-white">✓</span>}
                          </button>

                          {/* Icon */}
                          <Icon className={`h-5 w-5 shrink-0 ${cfg.color}`} />

                          {/* Info */}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <p className="truncate text-sm font-medium text-zinc-200">{doc.title}</p>
                              <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${cfg.bg} ${cfg.color}`}>{doc.file_type || "Other"}</span>
                            </div>
                            <div className="flex items-center gap-3 text-[11px] text-zinc-500 mt-0.5">
                              <span>{formatSize(doc.file_size)}</span>
                              <span>{formatDate(doc.created_at)}</span>
                              <span className="capitalize">id: {doc.id}</span>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            {isConfirming ? (
                              <div className="flex items-center gap-1">
                                <button onClick={() => handleDelete(doc.id)}
                                  className="rounded-lg bg-red-600 px-2.5 py-1 text-[11px] font-medium hover:bg-red-500">Confirm</button>
                                <button onClick={() => setDeleteConfirm(null)}
                                  className="rounded-lg bg-zinc-800 px-2.5 py-1 text-[11px] font-medium hover:bg-zinc-700">Cancel</button>
                              </div>
                            ) : (
                              <button onClick={() => setDeleteConfirm(doc.id)}
                                className="rounded-lg p-1.5 text-zinc-600 hover:text-red-400 hover:bg-red-950/30"
                                title="Delete document">
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
