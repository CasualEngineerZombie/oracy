import AppLayout from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StrandBadge from "@/components/StrandBadge";
import ModeBadge from "@/components/ModeBadge";
import { ArrowLeft, CheckCircle, Edit3, Clock, Play, ChevronDown } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  useAssessment,
  useAssessmentDraftReport,
  useAssessmentEvidence,
  useSignOffAssessment,
} from "@/lib/api";

const evidence = [
  { timestamp: "00:12–00:35", text: "Clear claim: \"The park is special because...\" followed by two supporting examples.", strand: "cognitive" as const, aiScore: 4 },
  { timestamp: "00:42–00:55", text: "Descriptive language: \"golden light filtering through the trees\" — strong imagery.", strand: "linguistic" as const, aiScore: 5 },
  { timestamp: "01:05–01:18", text: "Pace drops to a monotone here — reduced engagement.", strand: "physical" as const, aiScore: 2 },
  { timestamp: "01:40–01:55", text: "Strong conclusion — summarises key point and uses a rhetorical question.", strand: "cognitive" as const, aiScore: 4 },
];

const strandScores = [
  { strand: "physical" as const, aiScore: 3, teacherScore: null as number | null },
  { strand: "linguistic" as const, aiScore: 4, teacherScore: null as number | null },
  { strand: "cognitive" as const, aiScore: 4, teacherScore: null as number | null },
  { strand: "social-emotional" as const, aiScore: 3, teacherScore: null as number | null },
];

export default function TeacherReviewPage() {
  const { id } = useParams<{ id: string }>();
  const { data: assessment, isLoading: loadingAssessment } = useAssessment(id || "");
  const { data: draftReport, isLoading: loadingReport } = useAssessmentDraftReport(id || "");
  const { data: evidence, isLoading: loadingEvidence } = useAssessmentEvidence(id || "");
  const signOffMutation = useSignOffAssessment();

  const [scores, setScores] = useState(
    ["physical", "linguistic", "cognitive", "social_emotional"].map((strand) => ({
      strand,
      aiScore: 0,
      teacherScore: null as number | null,
    }))
  );
  const [confirmed, setConfirmed] = useState(false);

  // Update scores when draft report is loaded
  useEffect(() => {
    if (draftReport) {
      setScores([
        {
          strand: "physical",
          aiScore: draftReport.physical_score?.band || 0,
          teacherScore: null,
        },
        {
          strand: "linguistic",
          aiScore: draftReport.linguistic_score?.band || 0,
          teacherScore: null,
        },
        {
          strand: "cognitive",
          aiScore: draftReport.cognitive_score?.band || 0,
          teacherScore: null,
        },
        {
          strand: "social_emotional",
          aiScore: draftReport.social_emotional_score?.band || 0,
          teacherScore: null,
        },
      ]);
    }
  }, [draftReport]);

  const updateScore = (index: number, score: number) => {
    setScores((prev) =>
      prev.map((s, i) => (i === index ? { ...s, teacherScore: score } : s))
    );
  };

  const handleSignOff = async () => {
    if (!id) return;
    try {
      await signOffMutation.mutateAsync({
        assessmentId: id,
        data: {
          physical_band: scores[0].teacherScore || scores[0].aiScore,
          linguistic_band: scores[1].teacherScore || scores[1].aiScore,
          cognitive_band: scores[2].teacherScore || scores[2].aiScore,
          social_emotional_band: scores[3].teacherScore || scores[3].aiScore,
        },
      });
      setConfirmed(true);
    } catch (error) {
      console.error("Failed to sign off:", error);
    }
  };

  const getModeBadgeMode = (mode: string): "presentational" | "exploratory" | "collaborative" | "dialogic" | "persuasive" | "reflective" => {
    switch (mode) {
      case "formal":
        return "presentational";
      case "informal":
        return "exploratory";
      case "practice":
        return "collaborative";
      default:
        return "exploratory";
    }
  };

  const getStrandLabel = (strand: string): string => {
    switch (strand) {
      case "physical":
        return "Physical";
      case "linguistic":
        return "Linguistic";
      case "cognitive":
        return "Cognitive";
      case "social_emotional":
        return "Social-Emotional";
      default:
        return strand;
    }
  };

  const loading = loadingAssessment || loadingReport || loadingEvidence;

  if (loading) {
    return (
      <AppLayout role="teacher">
        <div className="max-w-3xl mx-auto space-y-6">
          <Link to="/teacher" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Loading assessment...
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  if (!assessment) {
    return (
      <AppLayout role="teacher">
        <div className="max-w-3xl mx-auto space-y-6">
          <Link to="/teacher" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Assessment not found
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout role="teacher">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link to="/teacher" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
              <span className="text-sm font-medium text-primary-foreground">
                {assessment.student_name.split(" ").map(n => n[0]).join("")}
              </span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">{assessment.student_name} — {assessment.prompt}</h1>
              <p className="text-xs text-muted-foreground">Submitted {new Date(assessment.created_at).toLocaleString()}</p>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            <ModeBadge mode={getModeBadgeMode(assessment.mode)} />
          </div>
        </motion.div>

        {/* Audio player placeholder */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Button size="sm" variant="outline" className="shrink-0 gap-1">
                <Play className="w-4 h-4" /> Play Recording
              </Button>
              <div className="flex-1 h-10 bg-secondary rounded-lg flex items-center gap-0.5 px-3">
                {Array.from({ length: 60 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-1 rounded-full bg-primary/30"
                    style={{ height: `${Math.random() * 100}%`, minHeight: "4px" }}
                  />
                ))}
              </div>
              <span className="text-xs text-muted-foreground shrink-0">1:55</span>
            </div>
          </CardContent>
        </Card>

        {/* Timestamped evidence */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">AI-Generated Evidence</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Review the AI's analysis below. Click timestamps to jump to that moment in the recording.
          </p>
          {loadingEvidence ? (
            <Card>
              <CardContent className="p-4 text-center text-muted-foreground">
                Loading evidence...
              </CardContent>
            </Card>
          ) : evidence && evidence.length > 0 ? (
            <div className="space-y-3">
              {evidence.map((ev, i) => (
                <Card key={i} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1.5">
                          <button className="flex items-center gap-1 text-xs text-primary font-mono hover:underline">
                            <Clock className="w-3 h-3" /> 
                            {new Date(ev.start_time * 1000).toISOString().substr(2, 5)}–
                            {new Date(ev.end_time * 1000).toISOString().substr(2, 5)}
                          </button>
                          <StrandBadge strand={ev.relevant_strands[0] as "physical" || "cognitive"} />
                        </div>
                        <p className="text-sm text-foreground">{ev.summary}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-4 text-center text-muted-foreground">
                No evidence available yet
              </CardContent>
            </Card>
          )}
        </div>

        {/* Teacher scoring */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">Confirm / Edit Scores</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {scores.map((s, i) => (
              <Card key={s.strand}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <StrandBadge strand={s.strand === "social_emotional" ? "social-emotional" : s.strand as "physical" | "linguistic" | "cognitive"} />
                    <span className="text-xs text-muted-foreground">AI: {s.aiScore}/5</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => updateScore(i, n)}
                        className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${
                          (s.teacherScore ?? s.aiScore) === n
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "bg-secondary text-muted-foreground hover:bg-accent"
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                    {s.teacherScore !== null && s.teacherScore !== s.aiScore && (
                      <span className="ml-2 text-xs text-warning flex items-center gap-1">
                        <Edit3 className="w-3 h-3" /> Edited
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Confirm button */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline">Add Teacher Note</Button>
          <Button
            onClick={handleSignOff}
            disabled={confirmed || signOffMutation.isPending}
            className="gap-2"
          >
            {signOffMutation.isPending ? (
              "Signing off..."
            ) : confirmed ? (
              <>
                <CheckCircle className="w-4 h-4" /> Confirmed
              </>
            ) : (
              "Confirm & Send Feedback"
            )}
          </Button>
        </div>
      </div>
    </AppLayout>
  );
}
