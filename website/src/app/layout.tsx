import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AetherGrid Sovereign | Complex-fuzzy Graph Transformers",
  description: "A production-ready digital twin orchestrator fusing live urban telemetry with variational quantum phase generators.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" style={{ scrollBehavior: 'smooth' }}>
      <body className={`${inter.className} antialiased bg-cantor-black text-white font-sans`}>
        {children}
      </body>
    </html>
  );
}
