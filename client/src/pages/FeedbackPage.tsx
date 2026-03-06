import AppLayout from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StrandBadge from "@/components/StrandBadge";
import ModeBadge from "@/components/ModeBadge";
import { Textarea } from "@/components/ui/textarea";
import {
  Star,
  Target,
  Dumbbell,
  Clock,
  ArrowLeft,
  CheckCircle,
  Play,
  AlertTriangle,
  Sparkles,
  MessageCircle,
  ChevronDown,
} from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

// --- Mock data aligned to Oracy Evaluation Contract outputs ---

const submissionMeta = {
  title: "My Favourite Place",
  mode: "presentational" as const,
  submittedAgo: "2 days ago",
  reviewedBy: "Ms Johnson",
  lowConfidence: false, // toggle to true to see confidence warning
  duration: "1:55",
};

const strandScores: {
  strand: "physical" | "linguistic" | "cognitive" | "social-emotional";
  score: 1 | 2 | 3 | 4;
  label: string;
  childLabel: string;
  emoji: string;
}[] = [
  { strand: "physical", score: 3, label: "Physical", childLabel: "How you sound", emoji: "🗣️" },
  { strand: "linguistic", score: 4, label: "Linguistic", childLabel: "Your words", emoji: "📝" },
  { strand: "cognitive", score: 4, label: "Cognitive", childLabel: "Your ideas", emoji: "🧠" },
  { strand: "social-emotional", score: 3, label: "Social & Emotional", childLabel: "Your audience", emoji: "💬" },
];

const scoreLabels: Record<number, { text: string; color: string }> = {
  1: { text: "Getting started", color: "bg-destructive/10 text-destructive" },
  2: { text: "Building up", color: "bg-warning/10 text-warning" },
  3: { text: "Doing well", color: "bg-primary/10 text-primary" },
  4: { text: "Brilliant!", color: "bg-success/10 text-success" },
};

const strengths = [
  {
    text: "You spoke clearly and at a steady pace — easy to follow!",
    transcript: "\"Today I'm going to tell you about my favourite place...\"",
    timestampLabel: "0:05 – 0:15",
    startMs: 5000,
    strand: "physical" as const,
  },
  {
    text: "Great describing words - 'golden light filtering through the trees' really painted a picture.",
    transcript: "\"...the golden light filtering through the trees made everything feel warm...\"",
    timestampLabel: "0:42 – 0:55",
    startMs: 42000,
    strand: "linguistic" as const,
  },
  {
    text: "You finished with a strong ending that wrapped everything up nicely.",
    transcript: "\"So that's why the park will always be my special place - don't you think everyone needs somewhere like that?\"",
    timestampLabel: "1:40 – 1:55",
    startMs: 100000,
    strand: "cognitive" as const,
  },
];

const nextSteps = [
  {
    text: "Try changing your speed — slow down for important bits, speed up for exciting parts.",
    transcript: "\"...and then there are the flowers and the bench and the pond and the birds...\"",
    timestampLabel: "1:05 – 1:18",
    startMs: 65000,
    strand: "physical" as const,
  },
  {
    text: "Add a question for your audience to make them feel included, like 'Have you ever...?'",
    strand: "social-emotional" as const,
    transcript: null,
    timestampLabel: null,
    startMs: null,
    isGlobal: true,
  },
  {
    text: "When you give a reason, try adding a specific example to make it stronger.",
    transcript: "\"I like it because it's peaceful...\"",
    timestampLabel: "0:30 – 0:38",
    startMs: 30000,
    strand: "cognitive" as const,
  },
];

const drill = {
  name: "The Power Pause",
  purpose: "Practise slowing down and pausing between your main ideas to keep your audience listening.",
  estimatedMinutes: 3,
  alignedStrand: "physical" as const,
  alignedMode: "presentational" as const,
  steps: [
    "Pick three sentences from your talk (or make up three facts about any topic).",
    "Say the first sentence, then pause and count silently to two.",
    "Say the second sentence a little slower than usual.",
    "Pause again — count to three this time.",
    "Say the third sentence at your normal speed and finish strong!",
    "Record yourself and listen back. Can you hear the pauses?",
  ],
};

const reflectionQuestions = [
  "What part of your talk are you most proud of?",
  "If you could redo one part, what would you change and why?",
];

// --- Component ---

export default function FeedbackPage() {
  const [reflections, setReflections] = useState<string[]>(["", ""]);
  const [reflectionsSaved, setReflectionsSaved] = useState(false);
  const [drillCompleted, setDrillCompleted] = useState(false);

  const handleSaveReflections = () => {
    setReflectionsSaved(true);
  };

  const handlePlayMoment = (startMs: number | null) => {
    if (startMs === null) return;
    // In real app: seek audio/video to startMs
    console.log(`Seeking to ${startMs}ms`);
  };

  return (
    <AppLayout role="pupil">
      <div className="max-w-2xl mx-auto space-y-6 pb-12">
        {/* Back link */}
        <Link
          to="/pupil"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <ModeBadge mode={submissionMeta.mode} />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {submissionMeta.title} — Your Feedback
          </h1>
          <p className="text-sm text-muted-foreground">
            Submitted {submissionMeta.submittedAgo} · Reviewed by {submissionMeta.reviewedBy}
          </p>
        </motion.div>

        {/* Low-confidence warning */}
        {submissionMeta.lowConfidence && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Card className="border-warning/30 bg-warning/5">
              <CardContent className="p-4 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground">Some feedback may be limited</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    The recording was a bit hard to hear in places, so your teacher has checked the scores carefully. If anything looks wrong, ask your teacher!
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Audio player */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Button size="sm" variant="outline" className="shrink-0 gap-1.5">
                <Play className="w-4 h-4" /> Listen Back
              </Button>
              <div className="flex-1 h-10 bg-secondary rounded-lg flex items-center gap-0.5 px-3">
                {Array.from({ length: 50 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-1 rounded-full bg-primary/30"
                    style={{ height: `${Math.random() * 100}%`, minHeight: "4px" }}
                  />
                ))}
              </div>
              <span className="text-xs text-muted-foreground shrink-0">{submissionMeta.duration}</span>
            </div>
          </CardContent>
        </Card>

        {/* Strand score cards — child-friendly 1-4 scale */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-1">How did you do?</h2>
          <p className="text-sm text-muted-foreground mb-4">Here are your scores across four areas of oracy.</p>
          <div className="grid grid-cols-2 gap-3">
            {strandScores.map((s, i) => {
              const level = scoreLabels[s.score];
              return (
                <motion.div
                  key={s.strand}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <Card className="overflow-hidden">
                    <CardContent className="p-4 text-center">
                      <span className="text-2xl mb-1 block">{s.emoji}</span>
                      <p className="text-sm font-medium text-foreground mb-1">{s.childLabel}</p>
                      {/* Score dots */}
                      <div className="flex items-center justify-center gap-1.5 mb-2">
                        {[1, 2, 3, 4].map((n) => (
                          <div
                            key={n}
                            className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                              n <= s.score
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {n}
                          </div>
                        ))}
                      </div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${level.color}`}>
                        {level.text}
                      </span>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Strengths */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-1">
              <Star className="w-5 h-5 text-success" />
              <h2 className="font-semibold text-foreground">3 things you did well</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Tap the play button to hear the exact moment from your talk.
            </p>
            <div className="space-y-3">
              {strengths.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.1 }}
                  className="p-3 rounded-lg bg-success/5 border border-success/10"
                >
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-4 h-4 text-success mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{s.text}</p>
                      {s.transcript && (
                        <p className="text-xs text-muted-foreground mt-1.5 italic truncate">
                          "{s.transcript}"
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        {s.timestampLabel && (
                          <button
                            onClick={() => handlePlayMoment(s.startMs)}
                            className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:underline"
                          >
                            <Play className="w-3 h-3" /> {s.timestampLabel}
                          </button>
                        )}
                        <StrandBadge strand={s.strand} className="text-[10px] px-1.5 py-0.5" />
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Next steps */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-5 h-5 text-warning" />
              <h2 className="font-semibold text-foreground">3 things to try next time</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              These ideas will help you improve. Some link to a moment in your talk.
            </p>
            <div className="space-y-3">
              {nextSteps.map((ns, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.1 }}
                  className="p-3 rounded-lg bg-warning/5 border border-warning/10"
                >
                  <div className="flex items-start gap-3">
                    <span className="w-5 h-5 rounded-full bg-warning/20 flex items-center justify-center text-xs font-bold text-warning shrink-0">
                      {i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{ns.text}</p>
                      {ns.transcript && (
                        <p className="text-xs text-muted-foreground mt-1.5 italic truncate">
                          "{ns.transcript}"
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        {ns.timestampLabel && ns.startMs !== null ? (
                          <button
                            onClick={() => handlePlayMoment(ns.startMs)}
                            className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:underline"
                          >
                            <Play className="w-3 h-3" /> {ns.timestampLabel}
                          </button>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">General tip</span>
                        )}
                        <StrandBadge strand={ns.strand} className="text-[10px] px-1.5 py-0.5" />
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Practice drill */}
        <Card className="border-primary/20 bg-primary/[0.02]">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-1">
              <Dumbbell className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-foreground">Your Practice Drill</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-3">
              Try this quick activity to practise what you learned. It takes about {drill.estimatedMinutes} minutes.
            </p>

            <div className="p-4 rounded-lg bg-card border mb-4">
              <h3 className="font-semibold text-foreground text-sm mb-1">{drill.name}</h3>
              <p className="text-sm text-muted-foreground mb-3">{drill.purpose}</p>
              <div className="flex items-center gap-2 mb-4 flex-wrap">
                <StrandBadge strand={drill.alignedStrand} className="text-[10px] px-1.5 py-0.5" />
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" /> ~{drill.estimatedMinutes} min
                </span>
              </div>
              <ol className="space-y-2">
                {drill.steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm">
                    <span className="w-5 h-5 rounded-full bg-secondary flex items-center justify-center text-xs font-semibold text-foreground shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-foreground">{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <Button
              variant={drillCompleted ? "secondary" : "default"}
              size="sm"
              className="gap-1.5"
              onClick={() => setDrillCompleted(!drillCompleted)}
            >
              {drillCompleted ? (
                <>
                  <CheckCircle className="w-4 h-4" /> Done!
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Mark as completed
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Reflection prompt */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-1">
              <MessageCircle className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-foreground">Think about your talk</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Write a few sentences for each question. Your answers are saved in your portfolio.
            </p>
            <div className="space-y-4">
              {reflectionQuestions.map((q, i) => (
                <div key={i}>
                  <label className="text-sm font-medium text-foreground block mb-1.5">
                    {i + 1}. {q}
                  </label>
                  <Textarea
                    placeholder="Write your thoughts here…"
                    value={reflections[i]}
                    onChange={(e) => {
                      const updated = [...reflections];
                      updated[i] = e.target.value;
                      setReflections(updated);
                      if (reflectionsSaved) setReflectionsSaved(false);
                    }}
                    rows={3}
                    className="text-sm"
                  />
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3 mt-4">
              <Button
                size="sm"
                onClick={handleSaveReflections}
                disabled={reflections.every((r) => r.trim() === "") || reflectionsSaved}
                className="gap-1.5"
              >
                {reflectionsSaved ? (
                  <>
                    <CheckCircle className="w-4 h-4" /> Saved
                  </>
                ) : (
                  "Save my reflections"
                )}
              </Button>
              {reflectionsSaved && (
                <span className="text-xs text-success">Added to your portfolio ✓</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
