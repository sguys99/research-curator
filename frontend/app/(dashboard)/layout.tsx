import AuthGuard from "@/components/auth/AuthGuard";
import DashboardHeader from "@/components/layout/DashboardHeader";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <DashboardHeader />
        <div className="mx-auto w-full max-w-6xl px-6 py-8">{children}</div>
      </div>
    </AuthGuard>
  );
}
