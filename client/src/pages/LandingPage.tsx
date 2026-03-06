import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Mic, BarChart3, ClipboardCheck, ArrowRight, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";
import OracyLogo from "@/components/OracyLogo";

const features = [
  {
    icon: <Mic className="w-6 h-6" />,
    title: "Record & Practice",
    description: "Pupils record oracy tasks with AI-powered formative feedback and next-step prompts.",
  },
  {
    icon: <ClipboardCheck className="w-6 h-6" />,
    title: "Teacher Review",
    description: "AI generates timestamped evidence for teachers to confirm, edit, and annotate.",
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: "Track Progress",
    description: "Strand-based and mode-tagged dashboards with baseline and endline comparisons.",
  },
];

const strands = [
  { label: "Physical", emoji: "🏃", colorClass: "border border-strand-physical text-strand-physical bg-transparent" },
  { label: "Linguistic", emoji: "💬", colorClass: "border border-strand-linguistic text-strand-linguistic bg-transparent" },
  { label: "Cognitive", emoji: "🧠", colorClass: "border border-strand-cognitive text-strand-cognitive bg-transparent" },
  { label: "Social & Emotional", emoji: "🤝", colorClass: "border border-strand-social-emotional text-strand-social-emotional bg-transparent" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="container flex items-center justify-between h-14 md:h-16 lg:h-[72px]">
          <OracyLogo variant="full" theme="light" linkTo="/" />
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">Pupil Login</Button>
            </Link>
            <Link to="/login">
              <Button size="sm">Teacher Login</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="wave-bg absolute inset-0 pointer-events-none" />
        <div className="container relative py-20 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-2xl mx-auto text-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-secondary text-secondary-foreground text-sm font-medium mb-6">
              <span>🎤</span> Voice 21 Aligned
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6">
              Oracy practice,{" "}
              <span className="text-navy-light">powered by AI.</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8 max-w-lg mx-auto">
              Help pupils develop confident communication skills with AI-supported practice and teacher-mediated assessment across all four oracy strands.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/live-demo">
                <Button size="lg" className="gap-2 text-base px-8 py-6 h-auto shadow-lg hover:shadow-xl transition-shadow">
                  🎤 Try a 60-Second Demo <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
            </div>
            <div className="flex items-center justify-center gap-4 mt-4">
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  Pupil Login
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="sm">
                  Teacher Dashboard
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Strands strip */}
      <section className="border-y border-border bg-card">
        <div className="container py-6">
          <div className="flex flex-wrap items-center justify-center gap-4">
            {strands.map((strand) => (
              <div
                key={strand.label}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${strand.colorClass}`}
              >
                <span>{strand.emoji}</span>
                {strand.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-foreground mb-3">How it works</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            AI supports teacher judgement — it never replaces it.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.5 }}
              className="bg-card rounded-xl border border-border p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center text-primary mb-4">
                {feature.icon}
              </div>
              <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="gradient-navy">
        <div className="container py-16 text-center">
          <h2 className="text-3xl font-bold text-primary-foreground mb-4">
            Ready to transform oracy in your school?
          </h2>
          <p className="text-primary-foreground/70 mb-8 max-w-md mx-auto">
            Start with presentational and exploratory talk — expand across all modes as your pupils grow.
          </p>
          <Link to="/login">
            <Button size="lg" variant="secondary" className="gap-2">
              Get Started <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card">
        <div className="container py-8 text-center text-sm text-muted-foreground">
          © 2026 oracy.ai · Child-safe · Privacy-first · Aligned to Voice 21
        </div>
      </footer>
    </div>
  );
}
