import { cn } from "@/lib/utils";

interface StrandBadgeProps {
  strand: "physical" | "linguistic" | "cognitive" | "social-emotional";
  className?: string;
}

const strandConfig = {
  physical: {
    label: "Physical",
    emoji: "🏃",
    bgClass: "bg-strand-physical-light text-strand-physical",
  },
  linguistic: {
    label: "Linguistic",
    emoji: "💬",
    bgClass: "bg-strand-linguistic-light text-strand-linguistic",
  },
  cognitive: {
    label: "Cognitive",
    emoji: "🧠",
    bgClass: "bg-strand-cognitive-light text-strand-cognitive",
  },
  "social-emotional": {
    label: "Social & Emotional",
    emoji: "🤝",
    bgClass: "bg-strand-social-emotional-light text-strand-social-emotional",
  },
};

export default function StrandBadge({ strand, className }: StrandBadgeProps) {
  const config = strandConfig[strand];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
        config.bgClass,
        className
      )}
    >
      {config.emoji} {config.label}
    </span>
  );
}
