import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStudents, useCohorts, useBulkImportStudents, useCreateCohort, type StudentListItem, type Cohort } from "@/lib/api/students";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Upload, Users, UserPlus, Trash2, AlertCircle, CheckCircle2, XCircle } from "lucide-react";

// Get current academic year
const getCurrentAcademicYear = () => {
  const now = new Date();
  const year = now.getFullYear();
  if (now.getMonth() >= 8) { // September onwards
    return `${year}-${year + 1}`;
  }
  return `${year - 1}-${year}`;
};

export default function StudentManagementPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Data fetching
  const { data: students, isLoading: studentsLoading } = useStudents();
  const { data: cohorts, isLoading: cohortsLoading } = useCohorts();
  
  // Mutations
  const bulkImport = useBulkImportStudents();
  const createCohort = useCreateCohort();
  
  // Local state
  const [selectedCohort, setSelectedCohort] = useState<string | null>(null);
  const [studentFilter, setStudentFilter] = useState("");
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [isCreateCohortDialogOpen, setIsCreateCohortDialogOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCohortId, setUploadCohortId] = useState<string>("");
  const [academicYear, setAcademicYear] = useState(getCurrentAcademicYear());
  const [newCohortName, setNewCohortName] = useState("");
  const [newCohortDescription, setNewCohortDescription] = useState("");
  
  // Filter students by cohort and search
  const filteredStudents = students?.filter(student => {
    const matchesCohort = !selectedCohort || true; // TODO: Filter by cohort
    const matchesSearch = !studentFilter || 
      student.full_name.toLowerCase().includes(studentFilter.toLowerCase()) ||
      student.email.toLowerCase().includes(studentFilter.toLowerCase());
    return matchesCohort && matchesSearch;
  });
  
  // Get student count per cohort
  const getCohortStudentCount = (cohortId: string) => {
    return students?.filter(s => true).length || 0; // TODO: Filter by actual cohort
  };
  
  // Handle CSV upload
  const handleUpload = async () => {
    if (!uploadFile) {
      toast({
        title: "Error",
        description: "Please select a CSV file",
        variant: "destructive",
      });
      return;
    }
    
    try {
      const result = await bulkImport.mutateAsync({
        file: uploadFile,
        cohort_id: uploadCohortId || undefined,
        academic_year: academicYear,
      });
      
      toast({
        title: "Import Complete",
        description: `Created: ${result.summary.total_created}, Updated: ${result.summary.total_updated}, Errors: ${result.summary.total_errors}`,
        variant: result.summary.total_errors > 0 ? "default" : "default",
      });
      
      setIsUploadDialogOpen(false);
      setUploadFile(null);
    } catch (error) {
      toast({
        title: "Import Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };
  
  // Handle cohort creation
  const handleCreateCohort = async () => {
    if (!newCohortName.trim()) {
      toast({
        title: "Error",
        description: "Cohort name is required",
        variant: "destructive",
      });
      return;
    }
    
    try {
      await createCohort.mutateAsync({
        name: newCohortName,
        description: newCohortDescription || undefined,
        academic_year: academicYear,
      });
      
      toast({
        title: "Cohort Created",
        description: `Successfully created "${newCohortName}"`,
      });
      
      setIsCreateCohortDialogOpen(false);
      setNewCohortName("");
      setNewCohortDescription("");
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create cohort",
        variant: "destructive",
      });
    }
  };
  
  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Student Management</h1>
          <p className="text-muted-foreground">Manage students, cohorts, and bulk import</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isCreateCohortDialogOpen} onOpenChange={setIsCreateCohortDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <UserPlus className="w-4 h-4 mr-2" />
                Create Cohort
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Cohort</DialogTitle>
                <DialogDescription>
                  Create a new class or group for organizing students.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="cohort-name">Cohort Name</Label>
                  <Input
                    id="cohort-name"
                    placeholder="e.g., Year 7A, Debate Club"
                    value={newCohortName}
                    onChange={(e) => setNewCohortName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cohort-description">Description (Optional)</Label>
                  <Textarea
                    id="cohort-description"
                    placeholder="Brief description of this cohort"
                    value={newCohortDescription}
                    onChange={(e) => setNewCohortDescription(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="academic-year">Academic Year</Label>
                  <Input
                    id="academic-year"
                    placeholder="e.g., 2025-2026"
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateCohortDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateCohort} disabled={createCohort.isPending}>
                  {createCohort.isPending ? "Creating..." : "Create Cohort"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Upload className="w-4 h-4 mr-2" />
                Import Students
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Bulk Import Students</DialogTitle>
                <DialogDescription>
                  Upload a CSV file to import or update students.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="csv-file">CSV File</Label>
                  <Input
                    id="csv-file"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Required columns: student_id, first_name, last_name, email
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cohort-select">Enroll in Cohort (Optional)</Label>
                  <Select value={uploadCohortId} onValueChange={setUploadCohortId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a cohort" />
                    </SelectTrigger>
                    <SelectContent>
                      {cohorts?.map((cohort) => (
                        <SelectItem key={cohort.id} value={cohort.id}>
                          {cohort.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="academic-year-import">Academic Year</Label>
                  <Input
                    id="academic-year-import"
                    placeholder="e.g., 2025-2026"
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                  />
                </div>
                <div className="bg-muted p-4 rounded-lg">
                  <h4 className="font-medium text-sm mb-2">CSV Format</h4>
                  <code className="text-xs block bg-background p-2 rounded">
                    student_id,first_name,last_name,email,date_of_birth,year_group,eal<br />
                    STU001,John,Doe,john.doe@school.com,2012-05-15,7,false
                  </code>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsUploadDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleUpload} disabled={bulkImport.isPending}>
                  {bulkImport.isPending ? "Importing..." : "Import Students"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      
      {/* Main Content */}
      <Tabs defaultValue="students" className="space-y-4">
        <TabsList>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="cohorts">Cohorts</TabsTrigger>
        </TabsList>
        
        {/* Students Tab */}
        <TabsContent value="students">
          <Card>
            <CardHeader>
              <CardTitle>Students</CardTitle>
              <CardDescription>
                View and manage students across all cohorts
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search by name or email..."
                    value={studentFilter}
                    onChange={(e) => setStudentFilter(e.target.value)}
                  />
                </div>
                <Select value={selectedCohort || "all"} onValueChange={(val) => setSelectedCohort(val === "all" ? null : val)}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="All Cohorts" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Cohorts</SelectItem>
                    {cohorts?.map((cohort) => (
                      <SelectItem key={cohort.id} value={cohort.id}>
                        {cohort.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* Students Table */}
              {studentsLoading ? (
                <div className="text-center py-8">Loading students...</div>
              ) : filteredStudents && filteredStudents.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Year Group</TableHead>
                      <TableHead>Added</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredStudents.map((student) => (
                      <TableRow key={student.id}>
                        <TableCell className="font-medium">{student.full_name}</TableCell>
                        <TableCell>{student.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{student.year_group || "N/A"}</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(student.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No students found</p>
                  <p className="text-sm">Import students using a CSV file</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Cohorts Tab */}
        <TabsContent value="cohorts">
          <Card>
            <CardHeader>
              <CardTitle>Cohorts</CardTitle>
              <CardDescription>
                Manage class groups and enrollments
              </CardDescription>
            </CardHeader>
            <CardContent>
              {cohortsLoading ? (
                <div className="text-center py-8">Loading cohorts...</div>
              ) : cohorts && cohorts.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {cohorts.map((cohort) => (
                    <Card key={cohort.id} className="cursor-pointer hover:border-primary transition-colors" onClick={() => navigate(`/teacher/cohorts/${cohort.id}`)}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">{cohort.name}</CardTitle>
                        <CardDescription>{cohort.academic_year}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Users className="w-4 h-4" />
                          <span>{cohort.students?.length || 0} students</span>
                        </div>
                        {cohort.description && (
                          <p className="mt-2 text-sm">{cohort.description}</p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <UserPlus className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No cohorts found</p>
                  <p className="text-sm">Create a cohort to organize students</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
