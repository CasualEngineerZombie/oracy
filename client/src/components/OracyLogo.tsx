import { Link } from "react-router-dom";
import oracyLogoFull from "@/assets/brand/oracy-logo-cropped.png";

/**
 * OracyLogo — single source of truth for logo rendering.
 *
 * Props:
 *  - variant: "full" (wordmark + icon) | "icon" (icon only, for narrow widths)
 *  - theme: "light" (default, for light backgrounds) | "dark" (for navy/dark headers)
 *  - linkTo: where the logo links (defaults to "/")
 *  - className: additional wrapper classes
 *
 * TODO: When final SVG assets are provided, replace the <img> sources below.
 *       Until then, the uploaded JPG is used for both variants.
 *       Add a separate icon-only asset when available.
 */

interface OracyLogoProps {
  variant?: "full" | "icon";
  theme?: "light" | "dark";
  linkTo?: string;
  className?: string;
}

export default function OracyLogo({
  variant = "full",
  theme = "light",
  linkTo = "/",
  className = "",
}: OracyLogoProps) {
  return (
    <Link
      to={linkTo}
      className={`logo-container flex items-center shrink-0 ${className}`}
      style={{ flexShrink: 0 }}
    >
      <img
        src={oracyLogoFull}
        alt="Oracy logo"
        className={`w-auto max-w-none object-contain h-[30px] md:h-[36px] lg:h-[44px] ${
          theme === "dark" ? "brightness-0 invert" : ""
        }`}
        style={{ maxHeight: "none", maxWidth: "none" }}
        draggable={false}
      />
    </Link>
  );
}
