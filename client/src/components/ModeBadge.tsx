import { cn } from "@/lib/utils";

interface ModeBadgeProps {
  mode: "presentational" | "exploratory" | "collaborative" | "dialogic" | "persuasive" | "reflective";
  className?: string;
}

const modeConfig = {
  presentational: { label: "Presentational Talk", color: "bg-primary/10 text-primary" },
  exploratory: { label: "Exploratory Talk", color: "bg-accent text-accent-foreground" },
  collaborative: { label: "Collaborative Talk", color: "bg-secondary text-secondary-foreground" },
  dialogic: { label: "Dialogic Listening", color: "bg-muted text-muted-foreground" },
  persuasive: { label: "Persuasive Talk", color: "bg-primary/10 text-primary" },
  reflective: { label: "Reflective Talk", color: "bg-accent text-accent-foreground" },
};

export default function ModeBadge({ mode, className }: ModeBadgeProps) {
  const config = modeConfig[mode];
  return (
    <span className={cn("inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium", config.color, className)}>
      {config.label}
    </span>
  );
}
