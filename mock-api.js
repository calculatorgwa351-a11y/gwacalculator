import express from 'express';
import cors from 'cors';

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Mock data
const MOCK_USERS = [
  { id: 1, username: "admin", email: "admin@example.com", is_admin: true },
  { id: 2, username: "student1", email: "student1@example.com", is_admin: false },
  { id: 3, username: "student2", email: "student2@example.com", is_admin: false },
];

const MOCK_GRADES = [
  { id: 1, subject: "Mathematics", grade: 85.5, user_id: 2 },
  { id: 2, subject: "Science", grade: 92.0, user_id: 2 },
  { id: 3, subject: "English", grade: 78.5, user_id: 2 },
  { id: 4, subject: "History", grade: 88.0, user_id: 2 },
];

const MOCK_POSTS = [
  { id: 1, title: "Welcome to GWA Calculator", content: "This is a sample post.", author_id: 1 },
  { id: 2, title: "Tips for Improving Grades", content: "Study regularly and ask questions.", author_id: 1 },
];

// Root endpoint
app.get('/', (req, res) => {
  res.json({ message: "GWA Calculator Mock API is running" });
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: "healthy" });
});

// Authentication endpoints
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  
  // Simple mock authentication
  if (username === "admin" && password === "adminpass") {
    return res.json({ access_token: "mock_admin_token", token_type: "bearer", user: MOCK_USERS[0] });
  } else if (username.startsWith("2024") && password === "password123") {
    return res.json({ access_token: "mock_student_token", token_type: "bearer", user: MOCK_USERS[1] });
  } else {
    return res.status(401).json({ detail: "Invalid credentials" });
  }
});

app.post('/api/register', (req, res) => {
  const userData = req.body;
  const newUser = { id: 4, ...userData };
  res.json({ message: "User registered successfully", user: newUser });
});

// User endpoints
app.get('/api/users/me', (req, res) => {
  res.json(MOCK_USERS[1]);
});

app.get('/api/users/:userId', (req, res) => {
  const userId = parseInt(req.params.userId);
  const user = MOCK_USERS.find(u => u.id === userId);
  if (user) {
    res.json(user);
  } else {
    res.status(404).json({ detail: "User not found" });
  }
});

// Grade endpoints
app.get('/api/grades', (req, res) => {
  res.json(MOCK_GRADES);
});

app.post('/api/grades', (req, res) => {
  const gradeData = req.body;
  const newGrade = { id: MOCK_GRADES.length + 1, ...gradeData };
  MOCK_GRADES.push(newGrade);
  res.json(newGrade);
});

app.put('/api/grades/:gradeId', (req, res) => {
  const gradeId = parseInt(req.params.gradeId);
  const gradeData = req.body;
  const index = MOCK_GRADES.findIndex(g => g.id === gradeId);
  
  if (index !== -1) {
    MOCK_GRADES[index] = { ...MOCK_GRADES[index], ...gradeData };
    res.json(MOCK_GRADES[index]);
  } else {
    res.status(404).json({ detail: "Grade not found" });
  }
});

app.delete('/api/grades/:gradeId', (req, res) => {
  const gradeId = parseInt(req.params.gradeId);
  const index = MOCK_GRADES.findIndex(g => g.id === gradeId);
  
  if (index !== -1) {
    MOCK_GRADES.splice(index, 1);
    res.json({ message: "Grade deleted successfully" });
  } else {
    res.status(404).json({ detail: "Grade not found" });
  }
});

// Analytics endpoints
app.get('/api/analytics/gwa/:userId', (req, res) => {
  const userId = parseInt(req.params.userId);
  const userGrades = MOCK_GRADES.filter(g => g.user_id === userId);
  
  if (userGrades.length === 0) {
    return res.json({ gwa: 0.0, total_subjects: 0 });
  }
  
  const total = userGrades.reduce((sum, grade) => sum + grade.grade, 0);
  const gwa = total / userGrades.length;
  
  res.json({ gwa: Math.round(gwa * 100) / 100, total_subjects: userGrades.length });
});

app.get('/api/analytics/honors/:userId', (req, res) => {
  const userId = parseInt(req.params.userId);
  
  // Get GWA first
  const userGrades = MOCK_GRADES.filter(g => g.user_id === userId);
  if (userGrades.length === 0) {
    return res.json({ honors: "No honors", gwa: 0.0 });
  }
  
  const total = userGrades.reduce((sum, grade) => sum + grade.grade, 0);
  const gwa = total / userGrades.length;
  const roundedGwa = Math.round(gwa * 100) / 100;
  
  let honors;
  if (roundedGwa >= 97.5) {
    honors = "Summa Cum Laude";
  } else if (roundedGwa >= 94.5) {
    honors = "Magna Cum Laude";
  } else if (roundedGwa >= 91.5) {
    honors = "Cum Laude";
  } else {
    honors = "No honors";
  }
  
  res.json({ honors, gwa: roundedGwa });
});

// Posts endpoints
app.get('/api/posts', (req, res) => {
  res.json(MOCK_POSTS);
});

app.post('/api/posts', (req, res) => {
  const postData = req.body;
  const newPost = { id: MOCK_POSTS.length + 1, ...postData };
  MOCK_POSTS.push(newPost);
  res.json(newPost);
});

// Start server
app.listen(PORT, 'localhost', () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`Frontend should be accessible at http://localhost:3000`);
});