import { useState, useCallback, useRef, useMemo } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import OracyLogo from "@/components/OracyLogo";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import {
  DemoResult,
  SAMPLE_RESULT,
  simulateProcessing,
} from "@/data/sampleDemoResult";
import {
  Mic,
  MicOff,
  Square,
  Play,
  RotateCcw,
  ChevronRight,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Trash2,
  ArrowLeft,
  Gauge,
  Timer,
  MessageSquare,
  MapPin,
  Bug,
} from "lucide-react";

type Step = "consent" | "record" | "processing" | "results";

/* ───── Submission model ───── */
interface Submission {
  id: string;
  audioUrl: string | null;
  audioBlob: Blob | null;
  durationMs: number;
  createdAt: string;
  status: "processing" | "ready" | "failed";
  result: DemoResult | null;
  isSample: boolean;
}

function generateSubmissionId(): string {
  return `sub_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

function formatTimestamp(t: number) {
  return formatTime(Math.round(t));
}

/* ───── Level Meter ───── */
function LevelMeter({ level }: { level: number }) {
  const bars = 20;
  return (
    <div className="flex items-end gap-0.5 h-8">
      {Array.from({ length: bars }).map((_, i) => {
        const threshold = i / bars;
        const active = level > threshold;
        return (
          <div
            key={i}
            className={`w-1.5 rounded-full transition-all duration-75 ${
              active
                ? i / bars > 0.7
                  ? "bg-destructive"
                  : "bg-success"
                : "bg-muted"
            }`}
            style={{ height: `${((i + 1) / bars) * 100}%` }}
          />
        );
      })}
    </div>
  );
}

/* ───── Structure Check ───── */
function StructureCheck({
  label,
  detected,
  timestamp,
}: {
  label: string;
  detected: boolean;
  timestamp: number | null;
}) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        {detected ? (
          <CheckCircle className="w-4 h-4 text-success" />
        ) : (
          <XCircle className="w-4 h-4 text-destructive" />
        )}
        <span className="text-sm text-foreground">{label}</span>
      </div>
      {detected && timestamp !== null && (
        <span className="text-xs text-muted-foreground font-mono">
          {formatTimestamp(timestamp)}
        </span>
      )}
    </div>
  );
}

/* ───── Evidence Pin ───── */
function EvidencePinCard({
  pin,
  index,
  audioRef,
}: {
  pin: DemoResult["evidencePins"][0];
  index: number;
  audioRef: React.RefObject<HTMLAudioElement | null>;
}) {
  return (
    <button
      onClick={() => {
        if (audioRef.current) {
          audioRef.current.currentTime = pin.timestamp;
          audioRef.current.play();
        }
      }}
      className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors text-left w-full"
    >
      <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
        {index + 1}
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">{pin.label}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {pin.description}
        </p>
        <span className="text-xs text-primary font-mono mt-1 inline-block">
          ▶ {formatTimestamp(pin.timestamp)}
        </span>
      </div>
    </button>
  );
}

/* ───── Transcript Skeleton ───── */
function TranscriptSkeleton() {
  return (
    <div className="space-y-2 p-4">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/6" />
    </div>
  );
}

/* ───── Debug Panel ───── */
function DebugPanel({ submission }: { submission: Submission | null }) {
  const [open, setOpen] = useState(false);

  if (!submission) return null;

  const audioDurationSec = submission.durationMs / 1000;
  const transcriptEnd =
    submission.result?.transcript?.length
      ? submission.result.transcript[submission.result.transcript.length - 1].end
      : 0;
  const segmentCount = submission.result?.transcript?.length ?? 0;
  const mismatch = Math.abs(audioDurationSec - transcriptEnd);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(!open)}
        className="gap-1 bg-card shadow-lg"
      >
        <Bug className="w-3 h-3" /> Debug
      </Button>
      {open && (
        <Card className="absolute bottom-10 right-0 w-80 shadow-xl">
          <CardContent className="p-3 text-xs font-mono space-y-1">
            <p>
              <strong>submissionId:</strong> {submission.id}
            </p>
            <p>
              <strong>status:</strong> {submission.status}
            </p>
            <p>
              <strong>isSample:</strong> {String(submission.isSample)}
            </p>
            <p>
              <strong>audioUrl:</strong>{" "}
              {submission.audioUrl ? "✓ blob URL" : "—"}
            </p>
            <p>
              <strong>audioDuration:</strong> {audioDurationSec.toFixed(1)}s
            </p>
            <p>
              <strong>transcriptSegments:</strong> {segmentCount}
            </p>
            <p>
              <strong>transcriptEnd:</strong> {transcriptEnd.toFixed(1)}s
            </p>
            {mismatch > 1.5 && submission.status === "ready" && (
              <p className="text-destructive font-bold">
                ⚠ Duration mismatch: {mismatch.toFixed(1)}s
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ═══════ MAIN PAGE ═══════ */
export default function LiveDemoPage() {
  const [step, setStep] = useState<Step>("consent");
  const [consented, setConsented] = useState(false);
  const [processingStage, setProcessingStage] = useState("");
  const [processingProgress, setProcessingProgress] = useState(0);

  // Single source of truth: current submission
  const [currentSubmission, setCurrentSubmission] = useState<Submission | null>(
    null
  );

  const recorder = useAudioRecorder(60);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Derived from submission only
  const result = currentSubmission?.status === "ready" ? currentSubmission.result : null;
  const audioUrl = currentSubmission?.audioUrl ?? null;

  /* Actions */
  const handleGrantPermission = useCallback(async () => {
    const ok = await recorder.requestPermission();
    if (ok) setStep("record");
  }, [recorder]);

  const handleStop = useCallback(() => {
    recorder.stop();

    setTimeout(() => {
      // Create submission from the exact audio blob
      const subId = generateSubmissionId();
      const blob = recorder.audioBlob;
      const url = recorder.audioUrl;
      const durationMs = recorder.seconds * 1000;

      const submission: Submission = {
        id: subId,
        audioUrl: url,
        audioBlob: blob,
        durationMs,
        createdAt: new Date().toISOString(),
        status: "processing",
        result: null,
        isSample: false,
      };

      console.log("[LiveDemo] Created submission", {
        submissionId: subId,
        audioUrl: url ? "blob URL present" : "null",
        durationMs,
      });

      setCurrentSubmission(submission);
      setStep("processing");

      // Run simulated processing (mock — real transcription TBD)
      simulateProcessing((stage, progress) => {
        setProcessingStage(stage);
        setProcessingProgress(progress);
      }).then((mockResult) => {
        // In a real implementation, the transcription service would
        // process submission.audioBlob and return real transcript data.
        // For now, we use mock data but bind it to this submission.
        setCurrentSubmission((prev) => {
          if (!prev || prev.id !== subId) return prev; // stale guard
          console.log("[LiveDemo] Submission ready", {
            submissionId: subId,
            transcriptSegments: mockResult.transcript.length,
            firstTimestamp: mockResult.transcript[0]?.start,
            lastTimestamp:
              mockResult.transcript[mockResult.transcript.length - 1]?.end,
          });
          return { ...prev, status: "ready", result: mockResult };
        });
        setStep("results");
      });
    }, 400);
  }, [recorder]);

  const handleLoadSample = useCallback(() => {
    const subId = generateSubmissionId();
    const submission: Submission = {
      id: subId,
      audioUrl: null,
      audioBlob: null,
      durationMs: 54000, // sample is ~54s
      createdAt: new Date().toISOString(),
      status: "processing",
      result: null,
      isSample: true,
    };

    console.log("[LiveDemo] Loading sample submission", { submissionId: subId });

    setCurrentSubmission(submission);
    setStep("processing");

    simulateProcessing((stage, progress) => {
      setProcessingStage(stage);
      setProcessingProgress(progress);
    }).then((sampleResult) => {
      setCurrentSubmission((prev) => {
        if (!prev || prev.id !== subId) return prev;
        return { ...prev, status: "ready", result: sampleResult };
      });
      setStep("results");
    });
  }, []);

  const handleTryAgain = useCallback(() => {
    // Clear current submission entirely before new recording
    setCurrentSubmission(null);
    recorder.reset();
    setStep("record");
  }, [recorder]);

  const handleDelete = useCallback(() => {
    setCurrentSubmission(null);
    recorder.reset();
    setStep("consent");
  }, [recorder]);

  return (
    <div className="min-h-screen bg-background">
      {/* Debug panel — always visible */}
      <DebugPanel submission={currentSubmission} />

      {/* Top bar */}
      <nav className="sticky top-0 z-50 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="container flex items-center justify-between h-14 md:h-16 lg:h-[72px]">
          <OracyLogo variant="full" theme="light" linkTo="/" />
          <Link to="/">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="w-4 h-4" /> Back
            </Button>
          </Link>
        </div>
      </nav>

      <div className="container max-w-3xl py-8 md:py-14 space-y-6">
        <AnimatePresence mode="wait">
          {/* ──── STEP 1: CONSENT + MIC CHECK ──── */}
          {step === "consent" && (
            <motion.div
              key="consent"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="space-y-6"
            >
              <div className="text-center">
                <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-3">
                  Try a 60-second demo
                </h1>
                <p className="text-muted-foreground max-w-lg mx-auto">
                  Record yourself speaking for up to 60 seconds and get instant
                  AI feedback on your delivery, structure, and presentation
                  skills.
                </p>
              </div>

              <Card>
                <CardContent className="p-6 space-y-5">
                  <div className="flex items-start gap-3">
                    <Checkbox
                      id="consent"
                      checked={consented}
                      onCheckedChange={(v) => setConsented(v === true)}
                    />
                    <label
                      htmlFor="consent"
                      className="text-sm text-foreground leading-relaxed cursor-pointer"
                    >
                      I agree to this demo recording being processed to generate
                      feedback. The recording is processed in-browser and{" "}
                      <strong>not stored on any server</strong>.
                    </label>
                  </div>

                  {recorder.permissionError && (
                    <div className="flex items-center gap-2 text-destructive text-sm">
                      <MicOff className="w-4 h-4" />
                      {recorder.permissionError}
                    </div>
                  )}

                  {recorder.permissionGranted && (
                    <div className="flex items-center gap-3">
                      <Mic className="w-5 h-5 text-success" />
                      <span className="text-sm text-foreground">
                        Mic connected
                      </span>
                      <LevelMeter level={recorder.level} />
                    </div>
                  )}

                  <div className="flex flex-col sm:flex-row gap-3">
                    {!recorder.permissionGranted ? (
                      <Button
                        size="lg"
                        disabled={!consented}
                        onClick={handleGrantPermission}
                        className="gap-2"
                      >
                        <Mic className="w-4 h-4" /> Allow Microphone
                      </Button>
                    ) : (
                      <Button
                        size="lg"
                        onClick={() => setStep("record")}
                        className="gap-2"
                      >
                        Continue <ChevronRight className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={handleLoadSample}
                    >
                      Load a sample recording
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ──── STEP 2: RECORD ──── */}
          {step === "record" && (
            <motion.div
              key="record"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="space-y-6"
            >
              <div className="text-center">
                <h1 className="text-2xl font-bold text-foreground mb-2">
                  Record your talk
                </h1>
                <p className="text-muted-foreground text-sm">
                  Speak about any topic for up to 60 seconds. Try: "My favourite
                  place" or "Why I love my hobby."
                </p>
              </div>

              <Card>
                <CardContent className="p-8 flex flex-col items-center gap-5">
                  <LevelMeter level={recorder.level} />

                  {/* Timer ring */}
                  <div className="relative flex items-center justify-center">
                    <svg className="w-36 h-36" viewBox="0 0 120 120">
                      <circle
                        cx="60"
                        cy="60"
                        r="54"
                        fill="none"
                        stroke="hsl(var(--muted))"
                        strokeWidth="6"
                      />
                      <circle
                        cx="60"
                        cy="60"
                        r="54"
                        fill="none"
                        stroke={
                          recorder.state === "recording"
                            ? "hsl(var(--destructive))"
                            : "hsl(var(--primary))"
                        }
                        strokeWidth="6"
                        strokeLinecap="round"
                        strokeDasharray={2 * Math.PI * 54}
                        strokeDashoffset={
                          2 * Math.PI * 54 * (1 - recorder.seconds / 60)
                        }
                        transform="rotate(-90 60 60)"
                        className="transition-all duration-1000 ease-linear"
                      />
                    </svg>
                    <span className="absolute text-3xl font-mono font-bold text-foreground">
                      {formatTime(recorder.seconds)}
                    </span>
                  </div>

                  {recorder.state === "idle" || recorder.state === "stopped" ? (
                    <Button
                      size="lg"
                      onClick={() => {
                        // Clear previous submission when starting new recording
                        setCurrentSubmission(null);
                        if (recorder.state === "stopped") recorder.reset();
                        recorder.start();
                      }}
                      className="gap-2"
                    >
                      <Play className="w-4 h-4" />{" "}
                      {recorder.state === "stopped"
                        ? "Record Again"
                        : "Start Recording"}
                    </Button>
                  ) : (
                    <Button
                      size="lg"
                      variant="destructive"
                      onClick={handleStop}
                      className="gap-2"
                    >
                      <Square className="w-4 h-4" /> Stop & Analyse
                    </Button>
                  )}

                  {recorder.state === "recording" && (
                    <p className="text-xs text-muted-foreground animate-pulse">
                      Recording…
                    </p>
                  )}
                </CardContent>
              </Card>

              <div className="text-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLoadSample}
                  className="text-muted-foreground"
                >
                  Or load a sample recording instead
                </Button>
              </div>
            </motion.div>
          )}

          {/* ──── STEP 3: PROCESSING ──── */}
          {step === "processing" && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="space-y-6"
            >
              <div className="text-center">
                <h1 className="text-2xl font-bold text-foreground mb-2">
                  Analysing your talk…
                </h1>
                <p className="text-muted-foreground text-sm">
                  This usually takes 5–10 seconds.
                </p>
              </div>

              <Card>
                <CardContent className="p-8 flex flex-col items-center gap-5">
                  <div className="w-full max-w-sm">
                    <Progress value={processingProgress} className="h-3" />
                  </div>
                  <motion.p
                    key={processingStage}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-sm font-medium text-primary"
                  >
                    {processingStage}
                  </motion.p>
                  {currentSubmission && (
                    <p className="text-xs text-muted-foreground font-mono">
                      Submission: {currentSubmission.id}
                    </p>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ──── STEP 4: RESULTS ──── */}
          {step === "results" && currentSubmission && (
            <motion.div
              key={`results-${currentSubmission.id}`}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              className="space-y-6"
            >
              <div className="text-center">
                <h1 className="text-2xl font-bold text-foreground mb-2">
                  Your Results
                </h1>
                {result && result.confidence < 0.7 && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-warning/10 text-warning text-sm font-medium">
                    <AlertTriangle className="w-4 h-4" />
                    Best-effort results — teacher review recommended
                  </div>
                )}
              </div>

              {/* Audio playback — keyed to submission */}
              {audioUrl && (
                <audio
                  ref={audioRef}
                  key={currentSubmission.id}
                  src={audioUrl}
                  controls
                  className="w-full"
                />
              )}

              {/* A: Transcript */}
              <Card>
                <CardContent className="p-5">
                  <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-primary" />
                    Transcript
                  </h2>
                  {currentSubmission.status === "processing" || !result ? (
                    <TranscriptSkeleton />
                  ) : result.transcript.length === 0 ? (
                    <div className="text-sm text-muted-foreground p-4 bg-secondary/30 rounded-lg">
                      Transcript unavailable for this submission.
                    </div>
                  ) : (
                    <div className="text-sm text-foreground leading-relaxed bg-secondary/30 rounded-lg p-4 max-h-48 overflow-y-auto">
                      {result.transcript.map((w, i) => (
                        <button
                          key={`${currentSubmission.id}-w-${i}`}
                          onClick={() => {
                            if (audioRef.current) {
                              audioRef.current.currentTime = w.start;
                              audioRef.current.play();
                            }
                          }}
                          className="hover:bg-primary/10 rounded px-0.5 transition-colors"
                          title={`${formatTimestamp(w.start)} (click to seek)`}
                        >
                          {w.text}{" "}
                        </button>
                      ))}
                    </div>
                  )}
                  {currentSubmission.isSample && (
                    <p className="text-xs text-muted-foreground mt-2 italic">
                      ⓘ This is pre-computed sample data, not from a live
                      recording.
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Only show analysis panels when result is ready */}
              {result ? (
                <>
                  {/* B: Physical Delivery */}
                  <Card>
                    <CardContent className="p-5">
                      <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                        <Gauge className="w-5 h-5 text-strand-physical" />
                        Physical Delivery
                      </h2>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-secondary/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-foreground">
                            {result.delivery.speechRateWPM}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Words/min
                          </p>
                        </div>
                        <div className="bg-secondary/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-foreground">
                            {Math.round(result.delivery.pauseRatio * 100)}%
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Pause ratio
                          </p>
                        </div>
                        <div className="bg-secondary/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-foreground">
                            {result.delivery.fillerWords.reduce(
                              (a, b) => a + b.count,
                              0
                            )}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Filler words
                          </p>
                        </div>
                        <div className="bg-secondary/50 rounded-lg p-3 text-center">
                          <p className="text-2xl font-bold text-foreground font-mono">
                            {formatTimestamp(result.delivery.longestPauseAt)}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Longest pause
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* C: Structure */}
                  <Card>
                    <CardContent className="p-5">
                      <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <Timer className="w-5 h-5 text-strand-cognitive" />
                        Structure Signals
                      </h2>
                      <div className="divide-y divide-border">
                        <StructureCheck
                          label="Opening / greeting"
                          detected={result.structure.opening.detected}
                          timestamp={result.structure.opening.timestamp}
                        />
                        <StructureCheck
                          label="Signpost / transition"
                          detected={result.structure.signpost.detected}
                          timestamp={result.structure.signpost.timestamp}
                        />
                        <StructureCheck
                          label="Example / evidence"
                          detected={result.structure.example.detected}
                          timestamp={result.structure.example.timestamp}
                        />
                        <StructureCheck
                          label="Conclusion"
                          detected={result.structure.conclusion.detected}
                          timestamp={result.structure.conclusion.timestamp}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Strengths + Next Steps */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="p-5">
                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-success" />
                          Strengths
                        </h3>
                        <ul className="space-y-2">
                          {result.strengths.map((s, i) => (
                            <li
                              key={i}
                              className="text-sm text-muted-foreground flex items-start gap-2"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-success mt-1.5 shrink-0" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-5">
                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                          <ChevronRight className="w-4 h-4 text-primary" />
                          Next Steps
                        </h3>
                        <ul className="space-y-2">
                          {result.nextSteps.map((s, i) => (
                            <li
                              key={i}
                              className="text-sm text-muted-foreground flex items-start gap-2"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                  {/* D: Evidence Pins */}
                  <Card>
                    <CardContent className="p-5">
                      <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <MapPin className="w-5 h-5 text-primary" />
                        Evidence Timeline
                      </h2>

                      <div className="relative h-6 bg-secondary rounded-full mb-4 overflow-visible">
                        {result.evidencePins.map((pin, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              if (audioRef.current) {
                                audioRef.current.currentTime = pin.timestamp;
                                audioRef.current.play();
                              }
                            }}
                            className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center hover:scale-125 transition-transform"
                            style={{
                              left: `${(pin.timestamp / 60) * 100}%`,
                            }}
                            title={pin.label}
                          >
                            {i + 1}
                          </button>
                        ))}
                      </div>

                      <div className="space-y-2">
                        {result.evidencePins.map((pin, i) => (
                          <EvidencePinCard
                            key={`${currentSubmission.id}-pin-${i}`}
                            pin={pin}
                            index={i}
                            audioRef={audioRef}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                /* Loading state for analysis */
                <div className="space-y-4">
                  <Skeleton className="h-40 w-full rounded-lg" />
                  <Skeleton className="h-32 w-full rounded-lg" />
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pb-8">
                <Button
                  size="lg"
                  onClick={handleTryAgain}
                  className="gap-2"
                >
                  <RotateCcw className="w-4 h-4" /> Try Again
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={handleDelete}
                  className="gap-2 text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" /> Delete This Recording
                </Button>
              </div>

              {currentSubmission.isSample && (
                <p className="text-center text-xs text-muted-foreground">
                  These results were generated from a built-in sample recording.
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
