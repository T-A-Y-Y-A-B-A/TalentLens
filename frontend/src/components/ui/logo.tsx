import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoSize = "sm" | "md" | "lg";

interface LogoProps {
  /** sm = 20px icon / text-base, md = 24px icon / text-xl, lg = 32px icon / text-2xl */
  size?: LogoSize;
  /** Show or hide the "TalentLens" wordmark. Default: true */
  showText?: boolean;
  /** Wrap the logo in a Next.js Link. Pass href to enable. */
  href?: string;
  className?: string;
}

const sizeMap: Record<LogoSize, { icon: number; text: string }> = {
  sm: { icon: 20, text: "text-base" },
  md: { icon: 24, text: "text-xl" },
  lg: { icon: 32, text: "text-2xl" },
};

/**
 * Hexagon icon uses a regular convex hexagon (flat-top orientation, same shape as
 * the reference image — 6-sided polygon with equal sides, solid fill).
 * Color: #6D5EF8 (indigo-violet, matches reference).
 */
function HexagonIcon({ size }: { size: number }) {
  // Flat-top regular hexagon points for a 100×100 viewBox
  // Points: (50±50·cos(30°·k), 50±50·sin(30°·k)) starting at top-right vertex
  const points =
    "75,6.7 100,50 75,93.3 25,93.3 0,50 25,6.7";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ flexShrink: 0 }}
    >
      <polygon points={points} fill="#6D5EF8" />
      {/* Inner "L" lettermark — subtle white mark centered in the hex */}
      <text
        x="50"
        y="67"
        textAnchor="middle"
        fill="white"
        fontSize="44"
        fontWeight="800"
        fontFamily="system-ui, -apple-system, sans-serif"
        letterSpacing="-2"
      >
        TL
      </text>
    </svg>
  );
}

function LogoContent({
  size = "md",
  showText = true,
  className,
}: Omit<LogoProps, "href">) {
  const { icon, text } = sizeMap[size];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-bold text-zinc-900 select-none",
        text,
        className
      )}
    >
      <HexagonIcon size={icon} />
      {showText && <span>TalentLens</span>}
    </span>
  );
}

export function Logo({ href, size = "md", showText = true, className }: LogoProps) {
  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          "inline-flex items-center gap-2 font-bold text-zinc-900 hover:opacity-80 transition-opacity",
          sizeMap[size].text,
          className
        )}
      >
        <HexagonIcon size={sizeMap[size].icon} />
        {showText && <span>TalentLens</span>}
      </Link>
    );
  }
  return <LogoContent size={size} showText={showText} className={className} />;
}
