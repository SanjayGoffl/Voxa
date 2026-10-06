"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

const BASE_LINKS = [
  { href: "/browse", label: "Browse" },
  { href: "/compare", label: "Compare" },
  { href: "/needs-review", label: "Needs Review" },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, loading } = useAuth();

  const links = [...BASE_LINKS];
  if (user?.role === "brand") {
    links.push({ href: "/brand/import", label: "Import" });
  }

  return (
    <header className="sticky top-0 z-20 glass-panel mx-4 mt-4 flex items-center justify-between rounded-2xl px-5 py-3 md:mx-8">
      <Link href="/" className="font-semibold tracking-tight">
        Retail Review Insights
      </Link>
      <nav className="flex items-center gap-1">
        {links.map((link) => (
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

        {!loading && (
          <>
            {user ? (
              <div className="ml-2 flex items-center gap-2">
                <span className="text-sm text-muted">
                  {user.display_name}
                  {user.role === "brand" && " (brand)"}
                </span>
                <Button
                  variant="ghost"
                  onClick={() => {
                    logout();
                    router.push("/");
                  }}
                >
                  Log out
                </Button>
              </div>
            ) : (
              <div className="ml-2 flex items-center gap-1">
                <Link href="/login">
                  <Button variant="ghost">Log in</Button>
                </Link>
                <Link href="/signup">
                  <Button variant="primary">Sign up</Button>
                </Link>
              </div>
            )}
          </>
        )}

        <ThemeToggle />
      </nav>
    </header>
  );
}
