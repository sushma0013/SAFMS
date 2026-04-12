# User Management System Plan
## Smart Attendance & Fee Management System

---

## 1. USER ROLES & ACCESS MATRIX

### Role Hierarchy
```
Admin
├── Full system access
├── Manage all users
├── View all reports
└── System configuration

Teacher
├── Generate QR codes (for own subjects)
├── Mark attendance manually
├── View attendance reports (own subjects)
├── Manage students (enrolled in courses)
├── NO access to fee system
└── Update profile

Student
├── Scan QR codes to mark attendance
├── View own attendance records
├── View own fee dashboard
├── Pay fees via Khalti
├── View payment history
└── Update profile
```

---

## 2. DATABASE MODELS REQUIRED

### Current Structure (Review)
```
✅ Profile (accounts.models)
   - user (OneToOne to Django User)
   - role (admin | teacher | student)
   - phone
   - student_id (for students)
   - full_name

✅ StudentProfile (attendance.models)
   - user (OneToOne to Django User)
   - student_id (unique)
   - full_name
   - phone
   - address
   - major
   - semester
   - academic_advisor (FK to User/Teacher)

✅ Subject (attendance.models)
   - name
   - code (unique)
   - teacher (FK to User)
   - students (M2M with User)
   - semester
   - department

✅ QRSession (attendance.models)
   - uuid (unique)
   - subject (FK)
   - created_by (FK to User/Teacher)
   - created_at
   - session_date
   - valid_until (15 min from creation)
   - qr_code (image)
   - is_closed
   - closed_at

✅ AttendanceRecord (attendance.models)
   - student (FK to User)
   - session (FK to QRSession)
   - subject (FK to Subject)
   - status (Present | Absent)
   - recorded_at
   - date
```

### Additional Fields to Consider Adding
```
🔄 Profile Model
   - Add: is_network_verified (for QR scanning on same network)
   - Add: last_network_ip (track network for security)
   - Add: department (for consistency across roles)

🔄 StudentProfile Model
   - Add: enrollment_status (Active | Inactive | Suspended)
   - Add: date_enrolled
   - Add: class_section (useful for filtering)

🔄 Subject Model
   - Add: is_active (to disable subjects)
   - Add: max_students (capacity)
   - Add: meeting_times (when class occurs)

🔄 QRSession Model
   - Add: ip_range (whitelist only specific IPs/network)
   - Add: location (building/room where class is held)
   - Add: network_ssid (optional, for verification)
```

---

## 3. AUTHENTICATION FLOW

### User Registration Path

```
Signup Page
    ↓
[User enters: email, password, name, role selection]
    ↓
CASE 1: Teacher Registration
    ├─ Verify email
    ├─ Create User (Django)
    ├─ Create Profile (role=teacher)
    ├─ Redirect to: Complete Teacher Profile
    │   (department, subject expertise, etc.)
    └─ Teacher Dashboard
    
CASE 2: Student Registration
    ├─ Verify email
    ├─ Create User (Django)
    ├─ Create Profile (role=student)
    ├─ Redirect to: Complete Student Profile
    │   (student_id, major, semester, etc.)
    └─ Student Dashboard

CASE 3: Admin/Staff Registration
    └─ Invite-only (created via Django admin)
```

### Login Flow

```
Login Page
    ↓
[Enter email & password]
    ↓
Authenticate via Django Auth
    ↓
Retrieve Profile.role
    ↓
REDIRECT based on role:
    ├─ role = "admin"    → /admin/dashboard/
    ├─ role = "teacher"  → /attendance:teacher_dashboard
    └─ role = "student"  → /attendance:student_dashboard
```

### Social Auth (Google OAuth)

```
Google Login Button
    ↓
[User clicks "Login with Google"]
    ↓
Set session: desired_role = "student" (currently)
    ↓
Redirect to Google OAuth2
    ↓
On callback, check/create Profile
    └─ If new user: Create as "student" by default
    └─ If existing: Use existing role
    ↓
Dashboard Redirect (based on role)
```

---

## 4. AUTHORIZATION & PERMISSIONS

### Role-Based Access Control (RBAC)

#### TEACHER Routes & Permissions
```
✅ /attendance/my-classes/              - View enrolled subjects
✅ /attendance/my-classes/<id>/         - View subject details
✅ /attendance/generate-qr/             - Generate QR for subject
✅ /attendance/active-sessions/         - View active QR sessions
✅ /attendance/close-session/<uuid>/    - Close QR session early
✅ /attendance/attendance-records/      - View students' attendance
✓ /attendance/student-detail/<id>/      - View specific student (in subject)
❌ /fees/                               - BLOCKED
❌ /admin/                              - BLOCKED (unless staff)
❌ /dashboard/manage-fees/              - BLOCKED
```

#### STUDENT Routes & Permissions
```
✅ /attendance/scan-qr/                 - Scan QR code form
✅ /attendance/mark-attendance/         - Mark attendance via QR
✅ /attendance/my-attendance/           - View own attendance
✅ /fees/my-dashboard/                  - View fee summary
✅ /fees/due-payments/                  - View due fees
✅ /fees/pay/                           - Khalti payment page
✅ /fees/payment-history/               - View past payments
✅ /fees/download-receipt/              - Download payment receipt
❌ /attendance/generate-qr/             - BLOCKED
❌ /admin/                              - BLOCKED
❌ /fees/manage-fees/                   - BLOCKED
❌ /fees/payment-requests/              - BLOCKED
```

#### ADMIN Routes & Permissions
```
✅ /admin/                              - Full Django admin
✅ /admin/users/                        - Manage all users
✅ /admin/roles/                        - Manage roles
✅ /admin/subjects/                     - Manage all subjects
✅ /admin/attendance/reports/           - Global attendance reports
✅ /admin/fees/reports/                 - Global fee reports
✅ /admin/fees/pending-requests/        - Approve/reject fee requests
✅ /dashboard/admin/                    - Admin dashboard
```

### Implementing Permissions in Django

```python
# accounts/models.py - Add Permission Groups

from django.contrib.auth.models import Permission, Group

# Create groups in migration or management command:
GROUPS = {
    'teacher': [
        'can_generate_qr',
        'can_view_attendance',
        'can_edit_own_profile',
    ],
    'student': [
        'can_scan_qr',
        'can_view_fees',
        'can_pay_fees',
        'can_edit_own_profile',
    ],
    'admin': [
        'all permissions'
    ]
}

# In views, use @permission_required decorator:
@permission_required('attendance.can_generate_qr')
def generate_qr(request):
    ...
```

---

## 5. QR CODE & NETWORK VALIDATION

### QR Generation by Teacher

```
Workflow:
1. Teacher clicks "Generate QR Code"
2. Check: Teacher is on campus network (optional IP validation)
3. Select Subject from list
4. System creates QRSession object:
   ├─ uuid = unique identifier
   ├─ subject = selected subject
   ├─ created_at = now()
   ├─ session_date = today
   ├─ valid_until = now() + 15 minutes
   ├─ is_closed = False
   └─ network_ip = request.META['REMOTE_ADDR'] (optional)
5. Generate QR code image containing:
   └─ URL: /attendance/mark/{uuid}/
6. Display QR code to teacher
7. QR code auto-expires after 15 min (disable in frontend)
8. Students can scan immediately

Security:
- Validate teacher owns the subject
- Validate subject exists and is active
- Rate limit QR generation (prevent spam)
- Log all QR generations for audit
```

### QR Scanning by Student

```
Workflow:
1. Student opens /attendance/scan-qr/
2. webcam/camera permission requested
3. Student scans QR code
4. Extract uuid from QR
5. Fetch QRSession by uuid
6. Validate:
   ├─ Session exists
   ├─ Session not expired (check: now() < valid_until)
   ├─ Session not closed (is_closed = False)
   ├─ Student enrolled in subject
   └─ Student is on same network as teacher (optional)
7. Create AttendanceRecord:
   ├─ student = logged-in user
   ├─ session = QRSession
   ├─ subject = QRSession.subject
   ├─ status = "Present"
   ├─ recorded_at = now()
   └─ date = today
8. Check unique_together constraint (student, session)
   └─ If already exists: "Already marked for this session"
9. Mark attendance
10. Show success message with timestamp

Error Cases:
- "QR code expired" (if now() > valid_until)
- "Session is closed" (if is_closed = True)
- "You are not enrolled in this subject"
- "You already marked attendance for this session"
- "QR code not found"
```

### Network Validation (Optional Enhancement)

```python
# Check if teacher and student on same network:

def get_network_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_same_network(teacher_ip, student_ip):
    """Check if IPs are on same subnet (e.g., 192.168.x.x)"""
    from ipaddress import ip_address, ip_network
    # Assume /24 subnet
    teacher_network = ip_network(f"{teacher_ip}/24", strict=False)
    return ip_address(student_ip) in teacher_network

# In QRSession:
teacher_ip = get_network_ip(request)
qr_session.network_ip = teacher_ip
qr_session.save()

# In scan_qr view:
student_ip = get_network_ip(request)
if not is_same_network(qr_session.network_ip, student_ip):
    raise ValidationError("You must be on the same network to scan")
```

---

## 6. FEE MANAGEMENT ACCESS

### STUDENT View (Has Access)

```
Dashboard /fees/my-dashboard/
├─ Total Fee: Rs. XXXX
├─ Paid Amount: Rs. XXXX
├─ Due Amount: Rs. XXXX
├─ Semester: 5th
├─ Due Date: 2025-04-30
└─ Button: "Pay Now" (if due > 0)

Due Fees List /fees/due-payments/
├─ Semester 5
│   ├─ Due: Rs. XXXX
│   ├─ Due Date: 2025-04-30
│   └─ Status: OVERDUE / DUE
└─ Semester 6 (future)

Payment History /fees/payment-history/
├─ Date        | Amount  | Method  | Status
├─ 2025-03-15  | Rs. 500 | KHALTI  | Completed
└─ 2025-02-10  | Rs. 1000| MANUAL  | Completed

Payment Page /fees/pay/
├─ Select semester to pay
├─ Amount to pay (auto-filled)
├─ Select payment method (KHALTI | MANUAL)
└─ Button: "Pay" → Khalti redirect
```

### TEACHER View (NO Access)

```
❌ Cannot access /fees/
❌ Cannot see student fee information
❌ Cannot approve payments
❌ Cannot manage fee structures
```

### ADMIN View (Has Full Access)

```
/admin/fees/
├─ Manage FeeStructure (set fees)
├─ View all Payments
├─ Approve PaymentRequests
├─ Generate fee reports
├─ Bulk set fees
└─ Send fee notifications
```

---

## 7. USER PROFILE MANAGEMENT

### Student Profile Completion

```
First Login → Incomplete Profile? 
    ↓
Redirect to /profile/complete/
    ↓
Form Fields:
├─ Student ID (automatic from registration)
├─ Full Name
├─ Phone Number
├─ Address
├─ Major (e.g., Computer Science)
├─ Semester (1-8)
├─ Date of Birth (optional)
└─ Profile Picture (optional)
    ↓
Save & Redirect to Dashboard
```

### Teacher Profile Completion

```
First Login → Create Profile?
    ↓
Redirect to /profile/create/
    ↓
Form Fields:
├─ Full Name
├─ Phone Number
├─ Department (e.g., CSE, ECE)
├─ Specialization (e.g., Web Dev, AI)
├─ Office Location
├─ Office Hours
└─ Profile Picture (optional)
    ↓
Save & Redirect to Dashboard
```

### Profile Update Routes

```
✅ /profile/edit/              - Edit own profile
✅ /profile/change-password/   - Change password
✅ /profile/settings/          - Notification settings
❌ Cannot edit other user profiles (unless admin)
```

---

## 8. SECURITY CONSIDERATIONS

### Authentication & Passwords

```
✅ Django's password hashing (PBKDF2)
✅ Password strength validator
✅ Login attempt rate limiting
✅ Session timeout (15 min idle)
✅ CSRF token on all forms
✅ HTTPS only (enforce in production)
```

### Authorization Checks

```python
# In every view that needs role check:

@login_required
def teacher_only_view(request):
    if request.user.profile.role != 'teacher':
        raise PermissionDenied("Teachers only")
    # ... rest of view

# Or use custom decorator:
def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.profile.role != role:
                raise PermissionDenied(f"{role.title()} access required")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@role_required('teacher')
def generate_qr(request):
    ...
```

### Audit Logging

```
Log all critical actions:
✅ User login/logout
✅ QR code generated (by whom, for which subject)
✅ Attendance marked (by which student, time)
✅ Fee payment (amount, method, status)
✅ Profile changes (what field, old → new value)
✅ Role changes (who changed, from → to)
```

### Data Privacy

```
✅ Students cannot see other students' attendance
✅ Students cannot see other students' fee info
✅ Teachers cannot see Student fee data
✅ Teachers can only see attendance for their subjects
✅ Payment data encrypted in database
```

---

## 9. IMPLEMENTATION ROADMAP

### Phase 1: Core User Management (Week 1)
```
✅ Already done:
   - Profile model with roles (admin, teacher, student)
   - StudentProfile model
   - Django auth integration
   - Google OAuth setup

TODO:
   - Add @role_required decorators to existing views
   - Create role-based dashboard redirects
   - Add permission_required decorators
   - Create profile completion flow for first login
```

### Phase 2: QR Code & Attendance Flow (Week 2-3)
```
TODO:
   - QRSession model (already exists)
   - AttendanceRecord model (already exists)
   - generate_qr view for teachers
   - scan_qr view for students
   - mark_attendance view
   - attendance report views
```

### Phase 3: Fee Management (Week 3-4)
```
TODO:
   - Verify teacher has NO access to fee views
   - Student fee dashboard with totals
   - Khalti payment integration
   - Payment history & receipts
```

### Phase 4: Security & Polish (Week 4-5)
```
TODO:
   - Audit logging
   - Rate limiting
   - Session timeout
   - Error handling improvements
   - Test coverage
```

---

## 10. FILES TO CREATE/UPDATE

```
accounts/
├─ decorators.py          # NEW - @role_required, @teacher_required, @student_required
├─ middleware.py          # NEW - Session timeout, audit logging
├─ models.py              # UPDATE - Add permission groups
├─ views.py               # UPDATE - Add role checks, profile completion
├─ urls.py                # UPDATE - Add profile routes
└─ templates/
    ├─ profile/complete.html      # NEW
    ├─ profile/edit.html          # NEW
    └─ profile/settings.html      # NEW

attendance/
├─ views.py              # UPDATE - Role checks on QR gen/scan
├─ decorators.py         # NEW - @teacher_required, @student_required
└─ templates/
    ├─ qr/generate.html           # Already exists (review)
    ├─ qr/scan.html               # Already exists (review)
    └─ qr/success.html            # Already exists (review)

fees/
├─ views.py              # NEW - Block teacher access, student fee dashboard
├─ decorators.py         # NEW - @student_required
└─ templates/
    ├─ fees/my-dashboard.html     # NEW
    ├─ fees/payment-history.html  # NEW
    └─ fees/pay.html              # NEW
```

---

## 11. KEY VALIDATION RULES

```
Teacher QR Generation:
✅ Must be logged in
✅ Must have role = "teacher"
✅ Must own the subject (subject.teacher == request.user)
✅ Subject must be active
✅ Subject must have enrolled students
✅ Cannot generate if another active session exists for same subject

Student QR Scanning:
✅ Must be logged in
✅ Must have role = "student"
✅ Must be enrolled in subject (subject.students.filter(id=user.id))
✅ QR code must exist
✅ QR code must not be expired (now() < valid_until)
✅ QR code must not be closed (is_closed = False)
✅ Must not already have marked attendance for this session
✅ (Optional) Must be on same network as teacher

Fee Access:
✅ Only students can see own fees
✅ Teachers CANNOT see fees (even their own)
✅ Only admins can manage FEES globally
```

---

## 12. SUMMARY TABLE

| Feature | Admin | Teacher | Student |
|---------|-------|---------|---------|
| Generate QR | ❌ | ✅ | ❌ |
| Scan QR | ❌ | ❌ | ✅ |
| View Attendance (own) | ❌ | ✅ | ✅ |
| View Attendance (others) | ✅ | ✅* | ❌ |
| Manage Subjects | ✅ | ❌** | ❌ |
| View Fees (own) | ❌ | ❌ | ✅ |
| View Fees (others) | ✅ | ❌ | ❌ |
| Pay Fees | ❌ | ❌ | ✅ |
| Approve Payments | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |

*Teachers can only view attendance for students in their subjects
**Teachers can only see subjects they teach

---

## Next Steps

1. Review this plan
2. Identify areas that need clarification
3. Start with Phase 1 implementation
4. Add decorators and permission checks
5. Test each role's access thoroughly
