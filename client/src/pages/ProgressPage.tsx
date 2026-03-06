import AppLayout from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StrandBadge from "@/components/StrandBadge";
import ModeBadge from "@/components/ModeBadge";
import {
  ArrowLeft,
  TrendingUp,
  Award,
  Target,
  ChevronRight,
  Play,
  Calendar,
  Mic,
  Filter,
} from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// --- Mock data ---

const strandProgress = [
  {
    strand: "physical" as const,
    emoji: "🗣️",
    childLabel: "How you sound",
    scores: [2, 2, 3, 3],
    current: 3,
    target: 4,
  },
  {
    strand: "linguistic" as const,
    emoji: "📝",
    childLabel: "Your words",
    scores: [2, 3, 3, 4],
    current: 4,
    target: 4,
  },
  {
    strand: "cognitive" as const,
    emoji: "🧠",
    childLabel: "Your ideas",
    scores: [3, 3, 3, 4],
    current: 4,
    target: 4,
  },
  {
    strand: "social-emotional" as const,
    emoji: "💬",
    childLabel: "Your audience",
    scores: [1, 2, 2, 3],
    current: 3,
    target: 4,
  },
];

const scoreLabels: Record<number, string> = {
  1: "Getting started",
  2: "Building up",
  3: "Doing well",
  4: "Brilliant!",
};

const badges = [
  {
    id: "clear-speaker",
    name: "Clear Speaker",
    emoji: "🎙️",
    description: "Scored 3+ on 'How you sound' three times in a row",
    earned: true,
    earnedDate: "Week 3",
  },
  {
    id: "word-wizard",
    name: "Word Wizard",
    emoji: "✨",
    description: "Scored 4 on 'Your words' in a presentational talk",
    earned: true,
    earnedDate: "Week 4",
  },
  {
    id: "idea-builder",
    name: "Idea Builder",
    emoji: "🏗️",
    description: "Used a claim + example + reason in one talk",
    earned: false,
    earnedDate: null,
  },
  {
    id: "audience-connector",
    name: "Audience Connector",
    emoji: "🤝",
    description: "Scored 4 on 'Your audience' — making listeners feel included",
    earned: false,
    earnedDate: null,
  },
];

const nextTarget = {
  strand: "social-emotional" as const,
  criterion: "Audience awareness",
  childExplanation: "Try speaking directly to your audience - ask them a question or say 'imagine this...'",
};

const portfolio = [
  {
    id: "4",
    title: "My Favourite Place",
    date: "12 Feb 2026",
    mode: "presentational" as const,
    score: 3.5,
    reviewed: true,
  },
  {
    id: "3",
    title: "How Rainbows Form",
    date: "5 Feb 2026",
    mode: "presentational" as const,
    score: 3.0,
    reviewed: true,
  },
  {
    id: "2",
    title: "The Amazing Octopus",
    date: "28 Jan 2026",
    mode: "presentational" as const,
    score: 2.5,
    reviewed: true,
  },
  {
    id: "1",
    title: "Introduce Yourself",
    date: "20 Jan 2026",
    mode: "presentational" as const,
    score: 2.0,
    reviewed: true,
  },
];

const weekLabels = ["Week 1", "Week 2", "Week 3", "Week 4"];

// --- Component ---

export default function ProgressPage({ role = "pupil" }: { role?: "pupil" | "teacher" }) {
  const [modeFilter, setModeFilter] = useState("presentational");

  return (
    <AppLayout role={role}>
      <div className="max-w-3xl mx-auto space-y-6 pb-12">
        <Link
          to={role === "pupil" ? "/pupil" : "/teacher"}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {role === "pupil" ? "My Progress" : "Class Progress — 7B"}
          </h1>
          <p className="text-sm text-muted-foreground">
            See how your oracy skills are growing over time.
          </p>
        </motion.div>

        {/* Mode filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <Select value={modeFilter} onValueChange={setModeFilter}>
            <SelectTrigger className="w-[200px] h-9 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="presentational">Presentational Talk</SelectItem>
              <SelectItem value="exploratory" disabled>
                Exploratory Talk (coming soon)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Strand growth cards — child-friendly visual */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-1">Your skills over time</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Each dot shows your score from a different talk. Watch them go up!
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {strandProgress.map((sp, idx) => (
              <motion.div
                key={sp.strand}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08 }}
              >
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{sp.emoji}</span>
                        <div>
                          <p className="text-sm font-medium text-foreground">{sp.childLabel}</p>
                          <p className="text-[10px] text-muted-foreground capitalize">{sp.strand.replace("-", " & ")}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-success font-medium">
                        <TrendingUp className="w-3.5 h-3.5" />
                        {sp.scores[sp.scores.length - 1] - sp.scores[0] > 0
                          ? `+${sp.scores[sp.scores.length - 1] - sp.scores[0]}`
                          : "—"}
                      </div>
                    </div>

                    {/* Simple dot-line chart */}
                    <div className="relative h-20 flex items-end">
                      {/* Grid lines */}
                      {[1, 2, 3, 4].map((level) => (
                        <div
                          key={level}
                          className="absolute left-0 right-0 border-t border-dashed border-border"
                          style={{ bottom: `${((level - 1) / 3) * 100}%` }}
                        />
                      ))}
                      {/* Dots and connecting lines */}
                      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        <polyline
                          fill="none"
                          stroke="hsl(var(--primary))"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          vectorEffect="non-scaling-stroke"
                          points={sp.scores
                            .map((s, i) => {
                              const x = (i / (sp.scores.length - 1)) * 100;
                              const y = 100 - ((s - 1) / 3) * 100;
                              return `${x},${y}`;
                            })
                            .join(" ")}
                        />
                      </svg>
                      {/* Dot overlays */}
                      {sp.scores.map((s, i) => (
                        <div
                          key={i}
                          className="absolute w-3 h-3 rounded-full bg-primary border-2 border-card"
                          style={{
                            left: `${(i / (sp.scores.length - 1)) * 100}%`,
                            bottom: `${((s - 1) / 3) * 100}%`,
                            transform: "translate(-50%, 50%)",
                          }}
                        />
                      ))}
                    </div>
                    {/* Week labels */}
                    <div className="flex justify-between mt-1">
                      {weekLabels.map((w) => (
                        <span key={w} className="text-[9px] text-muted-foreground">{w}</span>
                      ))}
                    </div>
                    {/* Current level */}
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Now: Level {sp.current}</span>
                      <span className="text-xs text-muted-foreground">Target: Level {sp.target}</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Badges — mastery-based */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-1">Your Badges</h2>
          <p className="text-sm text-muted-foreground mb-4">
            You earn badges by reaching specific skill levels — not just for trying!
          </p>
          <div className="grid grid-cols-2 gap-3">
            {badges.map((badge, i) => (
              <motion.div
                key={badge.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.08 }}
              >
                <Card className={badge.earned ? "" : "opacity-50"}>
                  <CardContent className="p-4 text-center">
                    <span className="text-3xl block mb-2">{badge.emoji}</span>
                    <p className="text-sm font-medium text-foreground mb-0.5">{badge.name}</p>
                    <p className="text-xs text-muted-foreground mb-2">{badge.description}</p>
                    {badge.earned ? (
                      <span className="inline-flex items-center gap-1 text-xs text-success font-medium">
                        <Award className="w-3 h-3" /> Earned {badge.earnedDate}
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground italic">Keep going!</span>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Next target */}
        <Card className="gradient-navy border-none">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-primary-foreground" />
              <h2 className="font-semibold text-primary-foreground">Your Next Target</h2>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-sm text-primary-foreground/90 mb-1">
                  Focus on: <span className="font-medium text-primary-foreground">{nextTarget.criterion}</span>
                </p>
                <p className="text-sm text-primary-foreground/70">{nextTarget.childExplanation}</p>
              </div>
              <StrandBadge
                strand={nextTarget.strand}
                className="shrink-0 bg-primary-foreground/10 text-primary-foreground text-[10px]"
              />
            </div>
          </CardContent>
        </Card>

        {/* Portfolio */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-1">My Portfolio</h2>
          <p className="text-sm text-muted-foreground mb-4">
            All your recordings and feedback in one place.
          </p>
          <div className="space-y-2">
            {portfolio.map((item) => (
              <Link key={item.id} to={`/pupil/feedback/${item.id}`}>
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                      <Mic className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{item.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="w-3 h-3" /> {item.date}
                        </span>
                        <ModeBadge mode={item.mode} className="text-[10px] px-1.5 py-0.5" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {/* Average score as simple level dots */}
                      <div className="flex items-center gap-0.5">
                        {[1, 2, 3, 4].map((n) => (
                          <div
                            key={n}
                            className={`w-2 h-2 rounded-full ${
                              n <= Math.round(item.score)
                                ? "bg-primary"
                                : "bg-muted"
                            }`}
                          />
                        ))}
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
