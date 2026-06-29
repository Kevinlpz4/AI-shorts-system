import type { Metadata } from "next";
import "./globals.css";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

export const metadata: Metadata = {
  title: "Content Discovery Dashboard — AI Shorts System",
  description:
    "Cyberpunk sci-fi control room for topic discovery, analysis, and approval.",
  icons: {
    icon: "/favicon.ico",
  },
};

/** Root layout de Next.js con DashboardLayout (sidebar + header + cyberpunk theme) */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <DashboardLayout>{children}</DashboardLayout>
      </body>
    </html>
  );
}
