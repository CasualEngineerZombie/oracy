import AppLayout from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import StrandBadge from "@/components/StrandBadge";
import ModeBadge from "@/components/ModeBadge";
import ProgressRing from "@/components/ProgressRing";
import { Mic, ArrowRight, Clock, Star } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAssessments, useCurrentUser } from "@/lib/api";
import { useMemo } from "react";

// Sample upcoming tasks for display
const sampleUpcomingTasks = [
  {
    id: "1",
    title: "My Favourite Place — 2 min presentation",
    mode: "presentational" as const,
    strand: "physical" as const,
    dueDate: "Today",
    unit: "Unit 3: Personal Narratives",
  },
  {
    id: "2",
    title: "Should school start later? — Group discussion",
    mode: "exploratory" as const,
    strand: "cognitive" as const,
    dueDate: "Tomorrow",
    unit: "Unit 3: Personal Narratives",
  },
];

// Sample recent feedback for display
const sampleRecentFeedback = [
  {
    id: "1",
    title: "Introduce Yourself",
    score: 78,
    strengths: ["Clear projection", "Good eye contact cues", "Logical structure"],
    date: "2 days ago",
  },
];

export default function PupilDashboard() {
  const { data: user } = useCurrentUser();
  const { data: assessments, isLoading } = useAssessments();

  // Process assessments to get upcoming and recent
  const { upcomingTasks, recentFeedback } = useMemo(() => {
    if (!assessments) {
      return { upcomingTasks: sampleUpcomingTasks, recentFeedback: sampleRecentFeedback };
    }

    const upcoming = assessments
      .filter((a) => a.status === "draft" || a.status === "recording")
      .slice(0, 3)
      .map((a) => ({
        id: a.id,
        title: a.prompt,
        mode: a.mode === "formal" ? "presentational" as const : a.mode === "informal" ? "exploratory" as const : "collaborative" as const,
        strand: "physical" as const,
        dueDate: new Date(a.created_at).toLocaleDateString(),
        unit: a.cohort_name,
      }));

    const recent = assessments
      .filter((a) => a.status === "completed")
      .slice(0, 3)
      .map((a) => ({
        id: a.id,
        title: a.prompt,
        score: 0, // Would need to fetch from draft report
        strengths: ["View feedback for details"],
        date: new Date(a.completed_at || a.created_at).toLocaleDateString(),
      }));

    return {
      upcomingTasks: upcoming.length > 0 ? upcoming : sampleUpcomingTasks,
      recentFeedback: recent.length > 0 ? recent : sampleRecentFeedback,
    };
  }, [assessments]);

  // Calculate strand progress (mock for now)
  const strandProgress = [
    { strand: "physical" as const, value: 72 },
    { strand: "linguistic" as const, value: 65 },
    { strand: "cognitive" as const, value: 80 },
    { strand: "social-emotional" as const, value: 58 },
  ];
  return (
    <AppLayout role="pupil">
      <div className="space-y-8">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {user ? `Welcome back, ${user.first_name} 👋` : "Loading... 👋"}
          </h1>
          <p className="text-muted-foreground">Pupil Dashboard</p>
        </motion.div>

        {/* Progress overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {strandProgress.map(({ strand, value }, i) => (
            <motion.div
              key={strand}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="text-center py-4">
                <CardContent className="flex flex-col items-center gap-2 p-0 px-4">
                  <ProgressRing value={value} size={64} strokeWidth={5} />
                  <StrandBadge strand={strand} />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Upcoming tasks */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">Upcoming Tasks</h2>
          {isLoading ? (
            <Card>
              <CardContent className="p-4 text-center text-muted-foreground">
                Loading tasks...
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {upcomingTasks.map((task) => (
                <Card key={task.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                      <Mic className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground text-sm truncate">{task.title}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <ModeBadge mode={task.mode} />
                        <StrandBadge strand={task.strand} />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3.5 h-3.5" /> {task.dueDate}
                      </span>
                      <Link to={`/pupil/task/${task.id}`}>
                        <Button size="sm" className="gap-1">
                          Start <ArrowRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Recent feedback */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">Recent Feedback</h2>
          {recentFeedback.length === 0 ? (
            <Card>
              <CardContent className="p-4 text-center text-muted-foreground">
                No recent feedback
              </CardContent>
            </Card>
          ) : (
            recentFeedback.map((fb) => (
              <Card key={fb.id}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-medium text-foreground">{fb.title}</p>
                      <p className="text-xs text-muted-foreground">{fb.date}</p>
                    </div>
                    {fb.score > 0 && (
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-success/10 text-success text-sm font-semibold">
                        <Star className="w-4 h-4" /> {fb.score}%
                      </div>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    {fb.strengths.map((s) => (
                      <div key={s} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-success shrink-0" />
                        {s}
                      </div>
                    ))}
                  </div>
                  <Link to={`/pupil/feedback/${fb.id}`}>
                    <Button variant="outline" size="sm" className="mt-4 gap-1">
                      View Full Feedback <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
