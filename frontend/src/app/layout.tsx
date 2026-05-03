import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "XR11 — Medical Report Generation",
  description:
    "XR11 assists clinicians by generating structured chest X-ray reports from multimodal AI—retrieval-augmented context, uncertainty estimates, and verification hooks against a local backend.",
  applicationName: "XR11",
  robots: { index: false, follow: false },
  openGraph: {
    title: "XR11 — Medical Report Generation",
    description:
      "Multimodal medical report generation for chest radiographs with structured findings, impressions, and safety-oriented tooling.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <header className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-zinc-200 px-4 py-3 lg:px-8 dark:border-zinc-800">
          <div className="flex min-w-0 flex-col gap-0.5">
            <span className="text-base font-bold tracking-tight lg:text-lg">
              XR11
            </span>
            <span className="max-w-xl text-xs leading-snug lg:text-sm">
              Multimodal Medical Report Generation
            </span>
          </div>
          <div
            className="flex shrink-0 items-center gap-2"
            aria-label="Assistant status"
          >
            <span
              className="size-2 shrink-0 rounded-full bg-green-500"
              aria-hidden
            />
            <span className="text-xs whitespace-nowrap lg:text-sm">
              AI Online
            </span>
          </div>
        </header>
        <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      </body>
    </html>
  );
}
