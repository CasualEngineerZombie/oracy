import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useCohorts } from "@/lib/api/students";
import { useBulkCreateAssessment, type AssessmentMode } from "@/lib/api/assessments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Clock, 
  Users, 
  FileText, 
  CalendarDays,
  Sparkles
} from "lucide-react";

const assessmentModes: { id: AssessmentMode; title: string; description: string; example: string }[] = [
  {
    id: "presenting",
    title: "Presenting",
    description: "Students present information to an audience",
    example: "Present your research findings on climate change",
  },
  {
    id: "explaining",
    title: "Explaining",
    description: "Students explain how something works or how to do something",
    example: "Explain how photosynthesis works",
  },
  {
    id: "persuading",
    title: "Persuading",
    description: "Students persuade others to take action or believe something",
    example: "Persuade the school to adopt a recycling program",
  },
];

const ageBands = [
  { id: "8-9", label: "Ages 8-9 (Year 4)" },
  { id: "9-10", label: "Ages 9-10 (Year 5)" },
  { id: "10-11", label: "Ages 10-11 (Year 6)" },
  { id: "11-12", label: "Ages 11-12 (Year 7)" },
  { id: "12-13", label: "Ages 12-13 (Year 8)" },
  { id: "13-14", label: "Ages 13-14 (Year 9)" },
  { id: "14-15", label: "Ages 14-15 (Year 10)" },
  { id: "15-16", label: "Ages 15-16 (Year 11)" },
];

const timeLimits = [
  { value: 60, label: "1 minute" },
  { value: 120, label: "2 minutes" },
  { value: 180, label: "3 minutes" },
  { value: 300, label: "5 minutes" },
  { value: 600, label: "10 minutes" },
];

export default function CreateAssessmentPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Data
  const { data: cohorts, isLoading: cohortsLoading } = useCohorts();
  const bulkCreateAssessment = useBulkCreateAssessment();
  
  // Wizard state
  const [currentStep, setCurrentStep] = useState(0);
  const [mode, setMode] = useState<AssessmentMode>("presenting" as AssessmentMode);
  const [ageBand, setAgeBand] = useState("");
  const [selectedCohortIds, setSelectedCohortIds] = useState<string[]>([]);
  const [customTopic, setCustomTopic] = useState("");
  const [timeLimit, setTimeLimit] = useState(180);
  const [scheduleDate, setScheduleDate] = useState<Date | undefined>(undefined);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  
  const steps = [
    { title: "Mode", description: "Select assessment type", icon: FileText },
    { title: "Template", description: "Choose prompt template", icon: Sparkles },
    { title: "Cohorts", description: "Select students", icon: Users },
    { title: "Schedule", description: "Set timing", icon: CalendarDays },
    { title: "Review", description: "Confirm details", icon: Check },
  ];
  
  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return !!mode;
      case 1:
        return !!ageBand && !!timeLimit;
      case 2:
        return selectedCohortIds.length > 0;
      case 3:
        return true; // Schedule is optional
      case 4:
        return true;
      default:
        return false;
    }
  };
  
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };
  
  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleSubmit = async () => {
    // Bulk create assessments for all selected cohorts
    try {
      let totalCreated = 0;
      
      for (const cohortId of selectedCohortIds) {
        const result = await bulkCreateAssessment.mutateAsync({
          cohort_id: cohortId,
          mode: mode,
          prompt: customTopic || `Complete the ${mode} task assigned by your teacher`,
          time_limit_seconds: timeLimit,
        });
        
        totalCreated += result.count;
      }
      
      toast({
        title: "Assessments Created",
        description: `Successfully created ${totalCreated} assessment(s)`,
      });
      
      navigate("/teacher");
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create assessments. Please try again.",
        variant: "destructive",
      });
    }
  };
  
  const toggleCohort = (cohortId: string) => {
    setSelectedCohortIds(prev => 
      prev.includes(cohortId)
        ? prev.filter(id => id !== cohortId)
        : [...prev, cohortId]
    );
  };
  
  return (
    <div className="container max-w-4xl mx-auto py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Create Assessment</h1>
        <p className="text-muted-foreground">
          Set up a new oracy assessment for your students
        </p>
      </div>
      
      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                index < currentStep
                  ? "bg-primary border-primary text-primary-foreground"
                  : index === currentStep
                  ? "border-primary text-primary"
                  : "border-muted-foreground text-muted-foreground"
              }`}
            >
              {index < currentStep ? (
                <Check className="w-5 h-5" />
              ) : (
                <step.icon className="w-5 h-5" />
              )}
            </div>
            {index < steps.length - 1 && (
              <div
                className={`w-16 md:w-24 h-0.5 mx-2 ${
                  index < currentStep ? "bg-primary" : "bg-muted"
                }`}
              />
            )}
          </div>
        ))}
      </div>
      
      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{steps[currentStep].title}</CardTitle>
          <CardDescription>{steps[currentStep].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Step 1: Mode Selection */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <RadioGroup
                value={mode}
                onValueChange={(v) => setMode(v as AssessmentMode)}
                className="grid gap-4 md:grid-cols-3"
              >
                {assessmentModes.map((m) => (
                  <Label
                    key={m.id}
                    className={`cursor-pointer border-2 rounded-lg p-4 hover:border-primary transition-colors ${
                      mode === m.id ? "border-primary bg-primary/5" : ""
                    }`}
                  >
                    <RadioGroupItem value={m.id} className="sr-only" />
                    <div className="font-medium">{m.title}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {m.description}
                    </div>
                    <div className="text-xs text-muted-foreground mt-2 italic">
                      Example: "{m.example}"
                    </div>
                  </Label>
                ))}
              </RadioGroup>
            </div>
          )}
          
          {/* Step 2: Template */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label>Age Band</Label>
                <Select value={ageBand} onValueChange={setAgeBand}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select age band" />
                  </SelectTrigger>
                  <SelectContent>
                    {ageBands.map((band) => (
                      <SelectItem key={band.id} value={band.id}>
                        {band.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Time Limit</Label>
                <Select 
                  value={String(timeLimit)} 
                  onValueChange={(v) => setTimeLimit(Number(v))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select time limit" />
                  </SelectTrigger>
                  <SelectContent>
                    {timeLimits.map((tl) => (
                      <SelectItem key={tl.value} value={String(tl.value)}>
                        {tl.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Custom Topic (Optional)</Label>
                <Textarea
                  placeholder="Enter a custom topic or leave blank for students to choose..."
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  If left blank, students will be prompted to choose their own topic
                </p>
              </div>
            </div>
          )}
          
          {/* Step 3: Cohorts */}
          {currentStep === 2 && (
            <div className="space-y-4">
              {cohortsLoading ? (
                <div className="text-center py-8">Loading cohorts...</div>
              ) : cohorts && cohorts.length > 0 ? (
                <div className="space-y-2">
                  {cohorts.map((cohort) => (
                    <div
                      key={cohort.id}
                      className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-muted/50 ${
                        selectedCohortIds.includes(cohort.id) ? "border-primary bg-primary/5" : ""
                      }`}
                      onClick={() => toggleCohort(cohort.id)}
                    >
                      <Checkbox
                        checked={selectedCohortIds.includes(cohort.id)}
                        onCheckedChange={() => toggleCohort(cohort.id)}
                      />
                      <div>
                        <div className="font-medium">{cohort.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {cohort.academic_year}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No cohorts found</p>
                  <p className="text-sm">Create a cohort first to assign assessments</p>
                </div>
              )}
              
              {selectedCohortIds.length > 0 && (
                <div className="mt-4">
                  <Badge variant="secondary">
                    {selectedCohortIds.length} cohort(s) selected
                  </Badge>
                </div>
              )}
            </div>
          )}
          
          {/* Step 4: Schedule */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="schedule"
                  checked={scheduleEnabled}
                  onCheckedChange={(checked) => setScheduleEnabled(checked === true)}
                />
                <Label htmlFor="schedule" className="cursor-pointer">
                  Schedule for later
                </Label>
              </div>
              
              {scheduleEnabled && (
                <div className="space-y-2">
                  <Label>Assessment Date & Time</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start">
                        <Clock className="mr-2 h-4 w-4" />
                        {scheduleDate ? (
                          scheduleDate.toLocaleString()
                        ) : (
                          "Pick a date and time"
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={scheduleDate}
                        onSelect={setScheduleDate}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground">
                    Students will see the assessment at the scheduled time
                  </p>
                </div>
              )}
              
              {!scheduleEnabled && (
                <div className="text-sm text-muted-foreground">
                  Assessments will be available immediately after creation
                </div>
              )}
            </div>
          )}
          
          {/* Step 5: Review */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Assessment Mode</div>
                  <div className="font-medium capitalize">{mode}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Age Band</div>
                  <div className="font-medium">{ageBand}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Time Limit</div>
                  <div className="font-medium">
                    {timeLimits.find((tl) => tl.value === timeLimit)?.label}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Cohorts</div>
                  <div className="font-medium">
                    {selectedCohortIds.length} cohort(s)
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">Scheduled</div>
                  <div className="font-medium">
                    {scheduleEnabled && scheduleDate
                      ? scheduleDate.toLocaleString()
                      : "Immediately"}
                  </div>
                </div>
                {customTopic && (
                  <div className="space-y-1 md:col-span-2">
                    <div className="text-sm text-muted-foreground">Topic</div>
                    <div className="font-medium">{customTopic}</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
        
        {/* Navigation */}
        <div className="flex justify-between p-6 border-t">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 0}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          {currentStep < steps.length - 1 ? (
            <Button onClick={handleNext} disabled={!canProceed()}>
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button 
              onClick={handleSubmit}
              disabled={createAssessment.isPending}
            >
              {createAssessment.isPending ? "Creating..." : "Create Assessment"}
              <Check className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}
