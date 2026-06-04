"use client";

import UploadZone from "@/components/UploadZone";
import type { UploadResponse } from "@/types";

export default function UploadPage() {
  function handleComplete(result: UploadResponse) {
    console.log("Upload complete:", result.filename);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload Document</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Supported: PDF, DOCX, CSV, XLSX
        </p>
      </div>
      <UploadZone onComplete={handleComplete} />
    </div>
  );
}
