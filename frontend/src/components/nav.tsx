"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";

const LINKS = [
  { href: "/", label: "Upload" },
  { href: "/products", label: "Products" },
  { href: "/compare", label: "Compare" },
  { href: "/needs-review", label: "Needs Review" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 glass-panel mx-4 mt-4 flex items-center justify-between rounded-2xl px-5 py-3 md:mx-8">
      <Link href="/" className="font-semibold tracking-tight">
        Retail Review Insights
      </Link>
      <nav className="flex items-center gap-1">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:text-[var(--foreground)]",
              pathname === link.href && "bg-[var(--accent-soft)] text-[var(--accent)]"
            )}
          >
            {link.label}
          </Link>
        ))}
        <ThemeToggle />
      </nav>
    </header>
  );
}
