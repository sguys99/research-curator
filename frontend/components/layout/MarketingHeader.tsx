import Image from "next/image";
import Link from "next/link";

const navItems = [
  { label: "About", href: "#about" },
  { label: "Workflow", href: "#workflow" },
  { label: "Contact", href: "#contact" },
];

export default function MarketingHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-transparent bg-white/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <Image
            src="/images/icon.png"
            alt="Research Curator"
            width={36}
            height={36}
            className="rounded-xl"
          />
          <span className="font-display">Research Curator</span>
        </Link>
        <nav className="hidden items-center gap-2 rounded-full bg-slate-100 p-1 text-sm md:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="rounded-full px-4 py-2 text-slate-600 transition-colors hover:text-slate-900"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="hidden rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 md:inline-flex"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}
