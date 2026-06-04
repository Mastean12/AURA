"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { uploadFileWithProgress } from "@/lib/api";
import type { UploadResponse } from "@/types";

const ALLOWED = ".csv,.docx,.pdf,.xlsx";

type UploadState =
  | { phase: "idle" }
  | { phase: "selected"; file: File }
  | { phase: "uploading"; file: File; progress: number }
  | { phase: "success"; file: File; result: UploadResponse }
  | { phase: "error"; file: File; message: string };

export default function UploadZone({
  onComplete,
}: {
  onComplete?: (result: UploadResponse) => void;
}) {
  const [state, setState] = useState<UploadState>({ phase: "idle" });
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectFile = useCallback((f: File) => {
    setState({ phase: "selected", file: f });
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) selectFile(f);
    },
    [selectFile]
  );

  const startUpload = useCallback(async () => {
    if (state.phase !== "selected") return;
    const file = state.file;
    console.log("[Upload] Starting upload:", {
      filename: file.name,
      size: file.size,
      type: file.type,
    });
    setState({ phase: "uploading", file, progress: 0 });
    try {
      const result = await uploadFileWithProgress(file, (pct) => {
        setState({ phase: "uploading", file, progress: pct });
      });
      console.log("[Upload] Success:", result);
      setState({ phase: "success", file, result });
      onComplete?.(result);
    } catch (e) {
      const msg = (e as Error).message;
      console.error("[Upload] Error:", msg);
      setState({ phase: "error", file, message: msg });
    }
  }, [state, onComplete]);

  const reset = useCallback(() => {
    setState({ phase: "idle" });
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const isDragTarget = state.phase === "idle" || state.phase === "selected";

  return (
    <div className="space-y-4">
      <div
        onDragOver={
          isDragTarget
            ? (e) => { e.preventDefault(); setDragOver(true); }
            : undefined
        }
        onDragLeave={isDragTarget ? () => setDragOver(false) : undefined}
        onDrop={isDragTarget ? handleDrop : undefined}
        onClick={
          state.phase === "idle"
            ? () => inputRef.current?.click()
            : undefined
        }
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
          dragOver
            ? "border-blue-400 bg-blue-950/30"
            : state.phase === "success"
            ? "border-emerald-700 bg-emerald-950/20"
            : "border-zinc-700 hover:border-zinc-500"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED}
          className="hidden"
          onChange={(e) => e.target.files?.[0] && selectFile(e.target.files[0])}
        />

        {state.phase === "idle" && (
          <>
            <Upload className="mb-4 h-10 w-10 text-zinc-500" />
            <p className="text-sm font-medium text-zinc-300">
              Drop a file here or click to browse
            </p>
            <p className="mt-1 text-xs text-zinc-600">
              PDF &bull; DOCX &bull; CSV &bull; XLSX
            </p>
          </>
        )}

        {state.phase === "success" && (
          <>
            <CheckCircle className="mb-3 h-10 w-10 text-emerald-400" />
            <p className="text-sm font-medium text-emerald-300">
              Upload complete
            </p>
            <button
              onClick={(e) => { e.stopPropagation(); reset(); }}
              className="mt-3 text-xs text-zinc-500 underline underline-offset-2 hover:text-zinc-300"
            >
              Upload another file
            </button>
          </>
        )}
      </div>

      {(state.phase === "selected" ||
        state.phase === "uploading" ||
        state.phase === "error") && (
        <div
          className={`flex items-center justify-between rounded-xl border px-5 py-4 ${
            state.phase === "error"
              ? "border-red-800 bg-red-950/20"
              : "border-zinc-800 bg-zinc-900/70"
          }`}
        >
          <div className="flex items-center gap-3 min-w-0">
            <File className="h-6 w-6 shrink-0 text-blue-400" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {state.file.name}
              </p>
              <p className="text-xs text-zinc-500">
                {(state.file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {state.phase === "selected" && (
              <>
                <button
                  onClick={startUpload}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500"
                >
                  Upload
                </button>
                <button
                  onClick={reset}
                  className="rounded-lg p-2 text-zinc-500 hover:text-zinc-300"
                >
                  <X className="h-4 w-4" />
                </button>
              </>
            )}

            {state.phase === "uploading" && (
              <div className="flex items-center gap-2 text-sm text-zinc-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                {state.progress}%
              </div>
            )}

            {state.phase === "error" && (
              <>
                <span className="flex items-center gap-1.5 text-sm text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  {state.message}
                </span>
                <button
                  onClick={reset}
                  className="rounded-lg p-2 text-zinc-500 hover:text-zinc-300"
                >
                  <X className="h-4 w-4" />
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {state.phase === "uploading" && (
        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${state.progress}%` }}
          />
        </div>
      )}

      {state.phase === "success" && (
        <div className="rounded-xl border border-emerald-800 bg-emerald-950/20 p-5">
          <div className="space-y-1.5 text-sm">
            <p>
              <span className="text-zinc-500">File:</span>{" "}
              <span className="text-zinc-200">{state.result.filename}</span>
            </p>
            <p>
              <span className="text-zinc-500">Size:</span>{" "}
              <span className="text-zinc-200">
                {(state.result.size / 1024).toFixed(1)} KB
              </span>
            </p>
            <p>
              <span className="text-zinc-500">Uploaded:</span>{" "}
              <span className="text-zinc-200">
                {new Date(state.result.upload_timestamp).toLocaleString()}
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
