import AppLayout from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ModeBadge from "@/components/ModeBadge";
import { Users, ClipboardCheck, BarChart3, ArrowRight, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAssessments, useCurrentUser, type AssessmentListItem } from "@/lib/api";
import { useMemo } from "react";

const stats = [
  { label: "Active Pupils", value: "—", icon: <Users className="w-5 h-5" /> },
  { label: "Pending Reviews", value: "—", icon: <ClipboardCheck className="w-5 h-5" /> },
  { label: "Tasks This Week", value: "—", icon: <BarChart3 className="w-5 h-5" /> },
];

// Sample pending reviews for display
const samplePendingReviews: Array<{
  id: string;
  pupilName: string;
  task: string;
  mode: "presentational" | "exploratory";
  aiScore: number;
  submittedAt: string;
}> = [
  {
    id: "1",
    pupilName: "Amara K.",
    task: "My Favourite Place — Presentation",
    mode: "presentational" as const,
    aiScore: 74,
    submittedAt: "35 min ago",
  },
  {
    id: "2",
    pupilName: "Leo T.",
    task: "Should school start later? — Discussion",
    mode: "exploratory" as const,
    aiScore: 68,
    submittedAt: "1 hour ago",
  },
  {
    id: "3",
    pupilName: "Priya M.",
    task: "My Favourite Place — Presentation",
    mode: "presentational" as const,
    aiScore: 82,
    submittedAt: "2 hours ago",
  },
];

export default function TeacherDashboard() {
  const { data: user } = useCurrentUser();
  const { data: assessments, isLoading } = useAssessments();

  // Compute stats from assessments
  const stats = useMemo(() => {
    if (!assessments) {
      return [
        { label: "Active Pupils", value: "—", icon: <Users className="w-5 h-5" /> },
        { label: "Pending Reviews", value: "—", icon: <ClipboardCheck className="w-5 h-5" /> },
        { label: "Tasks This Week", value: "—", icon: <BarChart3 className="w-5 h-5" /> },
      ];
    }

    const pendingCount = assessments.filter(
      (a) => a.status === "completed" || a.status === "processing"
    ).length;
    
    // Count tasks from this week
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const thisWeekCount = assessments.filter((a) => {
      const created = new Date(a.created_at);
      return created >= oneWeekAgo;
    }).length;

    // Get unique students count
    const uniqueStudents = new Set(assessments.map((a) => a.student_name)).size;

    return [
      { label: "Active Pupils", value: uniqueStudents.toString(), icon: <Users className="w-5 h-5" /> },
      { label: "Pending Reviews", value: pendingCount.toString(), icon: <ClipboardCheck className="w-5 h-5" /> },
      { label: "Tasks This Week", value: thisWeekCount.toString(), icon: <BarChart3 className="w-5 h-5" /> },
    ];
  }, [assessments]);

  // Filter pending reviews (completed assessments without signed reports)
  const pendingReviews = useMemo(() => {
    if (!assessments) return [];
    return assessments
      .filter((a) => a.status === "completed")
      .slice(0, 5);
  }, [assessments]);

  const getModeBadge = (mode: string): "presentational" | "exploratory" | "collaborative" | "dialogic" | "persuasive" | "reflective" => {
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
  return (
    <AppLayout role="teacher">
      <div className="space-y-8">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {user ? `Good morning, ${user.first_name} 📋` : "Loading... 📋"}
          </h1>
          <p className="text-muted-foreground">Teacher Dashboard</p>
        </motion.div>

        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card>
                <CardContent className="flex items-center gap-4 p-5">
                  <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center text-primary">
                    {stat.icon}
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Pending reviews */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" />
              Pending Reviews
            </h2>
            <Link to="/teacher/review">
              <Button variant="ghost" size="sm" className="gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
          <div className="space-y-3">
            {isLoading ? (
              <Card>
                <CardContent className="p-4 text-center text-muted-foreground">
                  Loading assessments...
                </CardContent>
              </Card>
            ) : pendingReviews.length === 0 ? (
              <Card>
                <CardContent className="p-4 text-center text-muted-foreground">
                  No pending reviews
                </CardContent>
              </Card>
            ) : (
              pendingReviews.map((review) => (
                <Card key={review.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center shrink-0">
                      <span className="text-sm font-medium text-primary-foreground">
                        {review.student_name.split(" ").map(n => n[0]).join("")}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground text-sm">{review.student_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{review.cohort_name}</p>
                      <div className="mt-1">
                        <ModeBadge mode={getModeBadge(review.mode)} />
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-semibold text-foreground">Status: {review.status}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(review.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Link to={`/teacher/review/${review.id}`}>
                      <Button size="sm" variant="outline" className="gap-1">
                        Review <ArrowRight className="w-3.5 h-3.5" />
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>

        {/* Quick insight */}
        <Card className="bg-secondary/50 border-none">
          <CardContent className="p-5">
            <p className="text-sm font-medium text-foreground mb-1">💡 Class Insight</p>
            <p className="text-sm text-muted-foreground">
              <strong>Physical strand</strong> is the weakest area across 7B this unit. 
              12 pupils scored below baseline for projection and pace. Consider a targeted warm-up activity next lesson.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
