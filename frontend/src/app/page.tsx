"use client";

import { generateReport } from "@/lib/api";
import axios from "axios";
import { useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type ChangeEvent,
} from "react";

const ACCEPT_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/jpg",
]);

const PIPELINE_STEPS = [
  "Retrieving similar cases...",
  "Running uncertainty analysis...",
  "Generating Round 1 report...",
  "Refining with Round 2...",
  "Assembling final report...",
] as const;

function isAcceptedImage(file: File): boolean {
  const t = file.type.toLowerCase();
  if (ACCEPT_TYPES.has(t)) return true;
  const n = file.name.toLowerCase();
  return (
    n.endsWith(".png") || n.endsWith(".jpg") || n.endsWith(".jpeg")
  );
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(fr.result as string);
    fr.onerror = () =>
      reject(fr.error ?? new Error("Could not read image file."));
    fr.readAsDataURL(file);
  });
}

function parseAxiosMessage(err: unknown): string {
  if (!axios.isAxiosError(err)) {
    return err instanceof Error ? err.message : "Something went wrong.";
  }
  const detail = err.response?.data as unknown;
  if (
    detail &&
    typeof detail === "object" &&
    "detail" in detail
  ) {
    const d = (detail as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
      return String((d[0] as { msg: unknown }).msg);
    }
  }
  if (typeof detail === "string") return detail;
  return err.message || "Request failed.";
}

export default function Home() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const stepIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null
  );

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const assignFile = useCallback((next: File | null) => {
    setError(null);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      if (!next || !isAcceptedImage(next)) return null;
      return URL.createObjectURL(next);
    });
    if (!next) {
      setFile(null);
      return;
    }
    if (!isAcceptedImage(next)) {
      setFile(null);
      setError("Please use a PNG or JPG/JPEG chest X-ray image.");
      return;
    }
    setFile(next);
  }, []);

  const openPicker = () => fileInputRef.current?.click();

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    assignFile(f ?? null);
    e.target.value = "";
  };

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    assignFile(f ?? null);
  };

  const handleGenerate = async () => {
    if (!file || loading) return;

    setError(null);
    setLoading(true);
    setStepIndex(0);

    if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
    stepIntervalRef.current = setInterval(() => {
      setStepIndex((i) =>
        Math.min(i + 1, PIPELINE_STEPS.length - 1)
      );
    }, 2400);

    try {
      const [result, imageUrl] = await Promise.all([
        generateReport(file),
        readFileAsDataUrl(file),
      ]);
      sessionStorage.setItem("reportData", JSON.stringify(result));
      sessionStorage.setItem("imageUrl", imageUrl);
      router.push("/report");
    } catch (err: unknown) {
      setError(parseAxiosMessage(err));
    } finally {
      if (stepIntervalRef.current) {
        clearInterval(stepIntervalRef.current);
        stepIntervalRef.current = null;
      }
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-full flex-col bg-zinc-50 dark:bg-zinc-950">
      <main className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-8 px-4 py-12 sm:max-w-xl">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            XR11 — Chest X-ray report
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
            Upload a PNG or JPG image to generate a structured radiology-style
            report via the local API.
          </p>
        </header>

        <label htmlFor="xray-upload" className="sr-only">
          Upload chest X-ray image
        </label>
        <input
          id="xray-upload"
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,.jpg,.jpeg"
          className="sr-only"
          onChange={onInputChange}
        />

        <button
          type="button"
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={openPicker}
          disabled={loading}
          className={`flex min-h-[180px] w-full flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 dark:focus-visible:ring-zinc-500 ${
            dragActive
              ? "border-indigo-500 bg-indigo-50 dark:border-indigo-400 dark:bg-indigo-950/30"
              : "border-zinc-300 bg-white hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-zinc-600"
          } disabled:pointer-events-none disabled:opacity-60`}
        >
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-200">
            Drag and drop your X-ray here
          </span>
          <span className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
            PNG or JPG · or click to browse
          </span>
        </button>

        {previewUrl ? (
          <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            {/* Blob URLs are not supported by next/image */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="Selected X-ray preview"
              className="mx-auto max-h-80 w-full object-contain"
            />
          </div>
        ) : null}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={!file || loading}
          className="h-11 rounded-lg bg-zinc-900 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 dark:disabled:bg-zinc-700 dark:disabled:text-zinc-400"
        >
          Generate Report
        </button>

        {loading ? (
          <div
            className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
            aria-live="polite"
          >
            <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Progress
            </p>
            <ol className="flex flex-col gap-3">
              {PIPELINE_STEPS.map((label, i) => {
                const done = i < stepIndex;
                const active = i === stepIndex;
                return (
                  <li
                    key={label}
                    className={`flex items-start gap-3 text-sm ${
                      active
                        ? "font-medium text-zinc-900 dark:text-zinc-100"
                        : done
                          ? "text-zinc-500 dark:text-zinc-400"
                          : "text-zinc-400 dark:text-zinc-600"
                    }`}
                  >
                    <span
                      className={`mt-1 size-2 shrink-0 rounded-full ${
                        done
                          ? "bg-emerald-500"
                          : active
                            ? "animate-pulse bg-indigo-500"
                            : "bg-zinc-300 dark:bg-zinc-600"
                      }`}
                      aria-hidden
                    />
                    <span>{label}</span>
                  </li>
                );
              })}
            </ol>
          </div>
        ) : null}

        {error ? (
          <div
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200"
          >
            {error}
          </div>
        ) : null}
      </main>
    </div>
  );
}
