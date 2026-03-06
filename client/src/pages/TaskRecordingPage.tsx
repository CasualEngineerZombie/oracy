import AppLayout from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StrandBadge from "@/components/StrandBadge";
import ModeBadge from "@/components/ModeBadge";
import { Mic, Square, Play, RotateCcw, Send, Clock, Info } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type RecordingState = "idle" | "recording" | "recorded";

export default function TaskRecordingPage() {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [seconds, setSeconds] = useState(0);

  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleStart = () => {
    setRecordingState("recording");
    setSeconds(0);
    // Simulate timer
    const interval = setInterval(() => {
      setSeconds((prev) => {
        if (prev >= 120) {
          clearInterval(interval);
          setRecordingState("recorded");
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  };

  return (
    <AppLayout role="pupil">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Task info */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <ModeBadge mode="presentational" />
            <StrandBadge strand="physical" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">My Favourite Place</h1>
          <p className="text-muted-foreground text-sm">
            Give a 2-minute presentation about your favourite place. Describe what makes it special 
            and why you enjoy being there. Focus on clear projection and varied pace.
          </p>
        </motion.div>

        {/* Success criteria */}
        <Card className="bg-secondary/50 border-none">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-4 h-4 text-primary" />
              <p className="text-sm font-medium text-foreground">Success Criteria</p>
            </div>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Project your voice so everyone can hear clearly
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Use descriptive language to paint a picture
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Structure your talk with a clear beginning, middle, and end
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Vary your pace — slow down for important points
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Recording area */}
        <Card>
          <CardContent className="p-8 flex flex-col items-center">
            <AnimatePresence mode="wait">
              {recordingState === "idle" && (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-4"
                >
                  <div className="w-24 h-24 rounded-full bg-secondary flex items-center justify-center">
                    <Mic className="w-10 h-10 text-primary" />
                  </div>
                  <p className="text-sm text-muted-foreground">Ready to record your presentation?</p>
                  <Button size="lg" onClick={handleStart} className="gap-2">
                    <Play className="w-4 h-4" /> Start Recording
                  </Button>
                </motion.div>
              )}

              {recordingState === "recording" && (
                <motion.div
                  key="recording"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-4"
                >
                  <div className="relative">
                    <div className="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center animate-pulse">
                      <Mic className="w-10 h-10 text-destructive" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-destructive animate-pulse" />
                  </div>
                  <div className="flex items-center gap-2 text-foreground">
                    <Clock className="w-4 h-4" />
                    <span className="text-2xl font-mono font-semibold">{formatTime(seconds)}</span>
                    <span className="text-sm text-muted-foreground">/ 2:00</span>
                  </div>
                  <Button
                    size="lg"
                    variant="destructive"
                    onClick={() => setRecordingState("recorded")}
                    className="gap-2"
                  >
                    <Square className="w-4 h-4" /> Stop Recording
                  </Button>
                </motion.div>
              )}

              {recordingState === "recorded" && (
                <motion.div
                  key="recorded"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-4 w-full"
                >
                  <div className="w-24 h-24 rounded-full bg-success/10 flex items-center justify-center">
                    <Mic className="w-10 h-10 text-success" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Recording complete — {formatTime(seconds)}
                  </p>
                  {/* Fake waveform */}
                  <div className="w-full h-12 bg-secondary rounded-lg flex items-center justify-center gap-0.5 px-4">
                    {Array.from({ length: 50 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 rounded-full bg-primary/40"
                        style={{ height: `${Math.random() * 100}%`, minHeight: "4px" }}
                      />
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setRecordingState("idle");
                        setSeconds(0);
                      }}
                      className="gap-2"
                    >
                      <RotateCcw className="w-4 h-4" /> Re-record
                    </Button>
                    <Button className="gap-2">
                      <Send className="w-4 h-4" /> Submit for Feedback
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
