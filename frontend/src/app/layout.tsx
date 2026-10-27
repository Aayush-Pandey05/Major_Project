import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Multi-Agent AI Data Analyst | Full-Stack Enterprise Platform",
  description: "Autonomous multi-agent platform for natural language data analysis, Isolation Forest anomaly detection, XGBoost sales forecasting, and read-only SQL querying.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full bg-slate-950">
      <body className={`${inter.className} min-h-full flex bg-slate-950 text-slate-100 antialiased overflow-hidden`}>
        {children}
      </body>
    </html>
  );
}
