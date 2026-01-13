# ARK-TOOLS Usage Examples
## Real-World Scenarios and Complete Workflows

This document provides concrete examples of using ARK-TOOLS in various real-world scenarios.

---

## 📋 Table of Contents

1. [Python Microservices Consolidation](#python-microservices-consolidation)
2. [React Component Library Cleanup](#react-component-library-cleanup)
3. [Legacy Java Codebase Modernization](#legacy-java-codebase-modernization)
4. [Enterprise API Gateway Optimization](#enterprise-api-gateway-optimization)
5. [DevOps Script Consolidation](#devops-script-consolidation)
6. [Machine Learning Pipeline Cleanup](#machine-learning-pipeline-cleanup)

---

## 1. Python Microservices Consolidation

### Scenario
You have 8 microservices with significant code duplication across user management, authentication, and data validation functions.

### Before Structure
```
microservices/
├── user-service/
│   ├── app.py                 # 234 lines
│   ├── models.py             # 156 lines  
│   ├── validation.py         # 89 lines
│   └── utils.py              # 123 lines
├── auth-service/
│   ├── app.py                # 267 lines
│   ├── models.py             # 134 lines (70% similar to user-service)
│   ├── validation.py         # 92 lines (85% similar to user-service)
│   └── jwt_utils.py          # 145 lines
├── profile-service/
│   ├── app.py                # 198 lines
│   ├── models.py             # 112 lines (60% similar to others)
│   └── helpers.py            # 78 lines
└── ... (5 more similar services)
```

### ARK-TOOLS Workflow

#### Step 1: Setup and Initialize
```bash
# Setup ARK-TOOLS (detects existing services)
ark-setup --mode quick
# This will find your existing PostgreSQL/Redis and inherit credentials

# Initialize project structure
cd microservices/
/scaffold-project

# Analyze the entire microservices directory
/ark-analyze directory=./microservices type=comprehensive languages=python
```

#### Expected Analysis Output
```
🔍 ARK-TOOLS Analysis Results
================================
📂 Discovery: 67 Python files found
🔧 Extraction: 234 functions, 45 classes extracted
🎯 Patterns Detected:
   • API endpoints: 89 (Flask routes)
   • Service functions: 156 (business logic)
   • Data models: 45 (SQLAlchemy/Pydantic)
   • Validation functions: 67 (input validation)
   • Utility functions: 78 (helpers)

🔍 Duplication Analysis:
   • Exact duplicates: 23 functions
   • Near duplicates (>85%): 45 functions
   • Semantic duplicates (>70%): 67 functions

💡 Consolidation Opportunities:
   1. User management (8 services → 2 unified)
   2. Authentication (5 services → 1 shared library)  
   3. Validation utilities (12 files → 3 modules)
   4. Database models (45 models → 28 consolidated)

📊 Estimated Impact:
   • Code reduction: 47%
   • Maintenance effort: -65%
   • Bug surface area: -52%
```

#### Step 2: Create Conservative Transformation Plan
```bash
/ark-transform --analysis-id abc123 --strategy conservative --min-group-size 3
```

#### Generated Transformation Plan
```json
{
  "plan_id": "plan_xyz789",
  "strategy": "conservative",
  "groups": [
    {
      "name": "user_management_unified",
      "type": "consolidation",
      "source_files": [
        "user-service/models.py",
        "auth-service/models.py", 
        "profile-service/models.py"
      ],
      "operations": [
        {
          "type": "merge",
          "target": "shared/models/user_models.py",
          "merge_strategy": "best_implementation"
        }
      ],
      "risk_level": "low",
      "estimated_reduction": "68%"
    },
    {
      "name": "validation_utilities",
      "type": "utility_consolidation", 
      "source_files": [
        "user-service/validation.py",
        "auth-service/validation.py",
        "profile-service/validation.py"
      ],
      "operations": [
        {
          "type": "consolidate",
          "target": "shared/utils/validation.py",
          "organization": "by_functionality"
        }
      ],
      "risk_level": "low",
      "estimated_reduction": "74%"
    }
  ]
}
```

#### Step 3: Generate Consolidated Code
```bash
# First, do a dry run to review changes
/ark-generate --plan-id plan_xyz789 --dry-run=true

# Review the preview, then generate
/ark-generate --plan-id plan_xyz789 --backup-original=true
```

#### Generated Structure
```
.ark_output/v_20260112_143022/
├── shared/
│   ├── models/
│   │   ├── user_models.py        # Unified user/auth/profile models
│   │   └── __init__.py
│   ├── utils/
│   │   ├── validation.py         # Consolidated validation functions
│   │   ├── jwt_utils.py          # Centralized JWT handling
│   │   └── __init__.py
│   └── __init__.py
├── services/
│   ├── user_management/
│   │   ├── api.py                # Combined user/profile APIs
│   │   ├── service.py            # Business logic layer
│   │   └── __init__.py
│   └── auth_service/
│       ├── api.py                # Streamlined auth API
│       ├── service.py            # Auth business logic
│       └── __init__.py
├── tests/
│   ├── test_user_models.py       # Generated comprehensive tests
│   ├── test_validation.py
│   ├── test_user_management.py
│   └── test_auth_service.py
└── migration/
    ├── migration_guide.md       # How to integrate changes
    └── compatibility_layer.py   # Backward compatibility
```

#### Step 4: Validation and Integration
```bash
# Test the consolidated code
cd .ark_output/v_20260112_143022/
python -m pytest tests/ -v --cov=shared --cov=services

# Results:
# tests/test_user_models.py::test_user_creation PASSED
# tests/test_validation.py::test_email_validation PASSED  
# tests/test_user_management.py::test_user_api PASSED
# Coverage: 94%
# All tests passed, no regressions detected
```

### Results Achieved
- **Code Reduction**: 2,847 lines → 1,423 lines (50% reduction)
- **Files Consolidated**: 24 files → 12 files
- **Duplicates Eliminated**: 67 duplicate functions → 0
- **Test Coverage**: Increased from 67% → 94%
- **Maintenance**: Single source of truth for user/auth logic

---

## 2. React Component Library Cleanup

### Scenario
Your React component library has grown organically with multiple similar components, inconsistent styling, and scattered utility functions.

### Before Structure
```typescript
components/
├── buttons/
│   ├── PrimaryButton.tsx         # 89 lines
│   ├── SecondaryButton.tsx       # 76 lines (85% similar)
│   ├── ActionButton.tsx          # 92 lines (80% similar)
│   └── SubmitButton.tsx          # 67 lines (75% similar)
├── forms/
│   ├── LoginForm.tsx             # 234 lines
│   ├── SignupForm.tsx            # 256 lines (65% similar)
│   ├── ContactForm.tsx           # 198 lines (60% similar)
│   └── validation/
│       ├── emailValidator.ts     # 34 lines
│       ├── validateEmail.ts      # 31 lines (95% duplicate)
│       └── formUtils.ts          # 45 lines
└── modals/
    ├── ConfirmModal.tsx          # 123 lines
    ├── AlertModal.tsx            # 119 lines (90% similar)
    └── InfoModal.tsx             # 115 lines (88% similar)
```

### ARK-TOOLS Workflow

#### Step 1: Analyze React Components
```bash
/ark-analyze directory=./components type=comprehensive languages=typescript,javascript
```

#### Analysis Results
```
🔍 React Component Analysis
===========================
📂 Discovery: 23 TypeScript files, 156 lines of duplicate code
🔧 Component Extraction: 47 React components identified

🎯 Component Patterns:
   • Button variants: 8 components (high similarity)
   • Form components: 12 components (medium similarity)
   • Modal components: 6 components (high similarity)
   • Utility functions: 15 scattered helpers

🔍 Prop Interface Analysis:
   • Similar prop patterns: 23 components could share interfaces
   • Inconsistent naming: onClick vs handleClick vs onPress
   • Style props: 34 different styling approaches

💡 Recommendations:
   1. Unified Button component with variant props
   2. Base Modal component with composition
   3. Centralized form validation library
   4. Consistent prop interfaces
```

#### Step 2: Transform React Components
```bash
/ark-transform --analysis-id abc123 --strategy moderate
/ark-generate --plan-id xyz789 --output-format=structured
```

#### Generated Unified Components
```typescript
// .ark_output/v_20260112_150000/components/Button/Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'action' | 'submit';
  size?: 'sm' | 'md' | 'lg';
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  loading = false,
  children,
  className,
  type = 'button',
}) => {
  const baseClasses = 'btn focus:outline-none transition-colors duration-200';
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    action: 'bg-green-600 hover:bg-green-700 text-white',
    submit: 'bg-purple-600 hover:bg-purple-700 text-white'
  };
  const sizeClasses = {
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg'
  };

  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    disabled && 'opacity-50 cursor-not-allowed',
    loading && 'cursor-wait',
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={classes}
    >
      {loading ? (
        <span className="flex items-center">
          <LoadingSpinner className="mr-2" />
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  );
};

// Backward compatibility exports
export const PrimaryButton = (props: Omit<ButtonProps, 'variant'>) => 
  <Button {...props} variant="primary" />;
export const SecondaryButton = (props: Omit<ButtonProps, 'variant'>) => 
  <Button {...props} variant="secondary" />;
export const ActionButton = (props: Omit<ButtonProps, 'variant'>) => 
  <Button {...props} variant="action" />;
export const SubmitButton = (props: Omit<ButtonProps, 'variant'>) => 
  <Button {...props} variant="submit" type="submit" />;
```

```typescript
// .ark_output/v_20260112_150000/components/Modal/Modal.tsx
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  type?: 'default' | 'confirm' | 'alert' | 'info';
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'md',
  type = 'default',
  children,
  actions
}) => {
  if (!isOpen) return null;

  const typeStyles = {
    default: 'border-gray-200',
    confirm: 'border-yellow-300',
    alert: 'border-red-300',
    info: 'border-blue-300'
  };

  const typeIcons = {
    default: null,
    confirm: <WarningIcon className="text-yellow-500" />,
    alert: <AlertIcon className="text-red-500" />,
    info: <InfoIcon className="text-blue-500" />
  };

  return (
    <div className="fixed inset-0 z-50 overflow-auto">
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose} />
        <div className={`relative bg-white rounded-lg shadow-xl ${sizeClasses[size]} ${typeStyles[type]}`}>
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center">
              {typeIcons[type]}
              <h3 className="ml-2 text-lg font-semibold">{title}</h3>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <CloseIcon />
            </button>
          </div>
          <div className="p-4">{children}</div>
          {actions && (
            <div className="flex justify-end p-4 border-t space-x-2">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Specialized modal components
export const ConfirmModal: React.FC<ConfirmModalProps> = ({ onConfirm, onCancel, ...props }) => (
  <Modal
    type="confirm"
    actions={
      <>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button variant="primary" onClick={onConfirm}>Confirm</Button>
      </>
    }
    {...props}
  />
);
```

#### Generated Tests
```typescript
// .ark_output/v_20260112_150000/tests/Button.test.tsx
import { render, fireEvent, screen } from '@testing-library/react';
import { Button, PrimaryButton, SecondaryButton } from '../components/Button';

describe('Button Component', () => {
  test('renders with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveTextContent('Click me');
    expect(button).toHaveClass('btn', 'bg-blue-600');
  });

  test('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('applies variant styles correctly', () => {
    render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-gray-200');
  });

  test('backward compatibility - PrimaryButton', () => {
    render(<PrimaryButton>Primary</PrimaryButton>);
    expect(screen.getByRole('button')).toHaveClass('bg-blue-600');
  });

  test('loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toHaveClass('cursor-wait');
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Results Achieved
- **Component Reduction**: 23 components → 8 unified components
- **Code Reduction**: 1,847 lines → 967 lines (48% reduction)
- **Consistency**: Single design system across all components
- **Backward Compatibility**: All existing usage continues to work
- **Type Safety**: Comprehensive TypeScript interfaces
- **Test Coverage**: 96% coverage with generated tests

---

## 3. Legacy Java Codebase Modernization

### Scenario  
A 10-year-old Java enterprise application with scattered CRUD operations, duplicated business logic, and inconsistent error handling.

### Before Structure
```java
// Multiple service classes with similar patterns
src/main/java/com/company/services/
├── UserService.java              // 456 lines
├── CustomerService.java          // 423 lines (70% similar CRUD)
├── ProductService.java           // 389 lines (65% similar CRUD)
├── OrderService.java             // 512 lines (60% similar CRUD)
└── utils/
    ├── ValidationUtils.java      // 234 lines
    ├── DataValidator.java        // 198 lines (85% similar)
    ├── StringHelper.java         // 145 lines
    └── StringUtils.java          // 156 lines (90% similar)
```

### ARK-TOOLS Workflow

#### Step 1: Analyze Java Codebase
```bash
/ark-analyze directory=./src/main/java type=comprehensive languages=java
```

#### Analysis Results
```
🔍 Java Enterprise Analysis
===========================
📂 Discovery: 45 Java files, 12,847 total lines
🔧 Extraction: 234 methods, 67 classes

🎯 Enterprise Patterns Detected:
   • CRUD Services: 23 classes with similar patterns
   • Repository Pattern: 15 repositories with duplicate methods
   • DTO Classes: 34 DTOs with overlapping fields
   • Validation Logic: 67 validation methods (45 duplicates)
   • Exception Handling: 89 try-catch blocks (inconsistent)

🔍 Code Quality Issues:
   • Generic Exception catching: 67 instances
   • Missing input validation: 34 methods
   • SQL injection risks: 12 potential vulnerabilities
   • Missing transaction boundaries: 23 methods

💡 Modernization Opportunities:
   1. Generic CRUD base service
   2. Centralized validation framework
   3. Consistent exception handling
   4. Repository pattern standardization
```

#### Step 2: Create Modernization Plan
```bash
/ark-transform --analysis-id abc123 --strategy moderate --preserve-tests=true
```

#### Generated Modernized Code
```java
// .ark_output/v_20260112_160000/services/GenericCrudService.java
@Service
public abstract class GenericCrudService<T, ID> {
    protected abstract JpaRepository<T, ID> getRepository();
    protected abstract String getEntityName();
    
    @Transactional(readOnly = true)
    public Optional<T> findById(ID id) {
        try {
            validateId(id);
            return getRepository().findById(id);
        } catch (Exception e) {
            log.error("Error finding {} with id: {}", getEntityName(), id, e);
            throw new ServiceException(String.format("Failed to find %s", getEntityName()), e);
        }
    }
    
    @Transactional
    public T save(T entity) {
        try {
            validateEntity(entity);
            T savedEntity = getRepository().save(entity);
            log.info("Successfully saved {} with id: {}", getEntityName(), getId(savedEntity));
            return savedEntity;
        } catch (ValidationException e) {
            throw e; // Re-throw validation exceptions
        } catch (Exception e) {
            log.error("Error saving {}: {}", getEntityName(), entity, e);
            throw new ServiceException(String.format("Failed to save %s", getEntityName()), e);
        }
    }
    
    @Transactional
    public void deleteById(ID id) {
        try {
            validateId(id);
            if (!getRepository().existsById(id)) {
                throw new EntityNotFoundException(String.format("%s not found with id: %s", getEntityName(), id));
            }
            getRepository().deleteById(id);
            log.info("Successfully deleted {} with id: {}", getEntityName(), id);
        } catch (EntityNotFoundException e) {
            throw e; // Re-throw not found exceptions
        } catch (Exception e) {
            log.error("Error deleting {} with id: {}", getEntityName(), id, e);
            throw new ServiceException(String.format("Failed to delete %s", getEntityName()), e);
        }
    }
    
    @Transactional(readOnly = true)
    public Page<T> findAll(Pageable pageable) {
        try {
            return getRepository().findAll(pageable);
        } catch (Exception e) {
            log.error("Error finding all {}", getEntityName(), e);
            throw new ServiceException(String.format("Failed to retrieve %s list", getEntityName()), e);
        }
    }
    
    protected void validateId(ID id) {
        if (id == null) {
            throw new ValidationException(String.format("%s ID cannot be null", getEntityName()));
        }
    }
    
    protected abstract void validateEntity(T entity);
    protected abstract ID getId(T entity);
}

// .ark_output/v_20260112_160000/services/UserService.java
@Service
@Slf4j
public class UserService extends GenericCrudService<User, Long> {
    
    @Autowired
    private UserRepository userRepository;
    
    @Override
    protected JpaRepository<User, Long> getRepository() {
        return userRepository;
    }
    
    @Override
    protected String getEntityName() {
        return "User";
    }
    
    @Override
    protected void validateEntity(User user) {
        if (user == null) {
            throw new ValidationException("User cannot be null");
        }
        if (StringUtils.isBlank(user.getEmail())) {
            throw new ValidationException("User email is required");
        }
        if (!ValidationUtils.isValidEmail(user.getEmail())) {
            throw new ValidationException("Invalid email format");
        }
        if (StringUtils.isBlank(user.getUsername())) {
            throw new ValidationException("Username is required");
        }
    }
    
    @Override
    protected Long getId(User user) {
        return user.getId();
    }
    
    // User-specific business methods
    @Transactional(readOnly = true)
    public Optional<User> findByEmail(String email) {
        try {
            ValidationUtils.validateEmail(email);
            return userRepository.findByEmail(email);
        } catch (Exception e) {
            log.error("Error finding user by email: {}", email, e);
            throw new ServiceException("Failed to find user by email", e);
        }
    }
    
    @Transactional(readOnly = true)
    public boolean existsByUsername(String username) {
        try {
            ValidationUtils.validateRequired(username, "Username");
            return userRepository.existsByUsername(username);
        } catch (Exception e) {
            log.error("Error checking username existence: {}", username, e);
            throw new ServiceException("Failed to check username availability", e);
        }
    }
}

// .ark_output/v_20260112_160000/utils/ValidationUtils.java
@Component
@Slf4j
public final class ValidationUtils {
    
    private static final String EMAIL_PATTERN = 
        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$";
    private static final Pattern EMAIL_REGEX = Pattern.compile(EMAIL_PATTERN);
    
    private ValidationUtils() {
        // Utility class - prevent instantiation
    }
    
    public static void validateRequired(Object value, String fieldName) {
        if (value == null) {
            throw new ValidationException(String.format("%s is required", fieldName));
        }
        if (value instanceof String && StringUtils.isBlank((String) value)) {
            throw new ValidationException(String.format("%s cannot be empty", fieldName));
        }
    }
    
    public static void validateEmail(String email) {
        validateRequired(email, "Email");
        if (!isValidEmail(email)) {
            throw new ValidationException("Invalid email format: " + email);
        }
    }
    
    public static boolean isValidEmail(String email) {
        return email != null && EMAIL_REGEX.matcher(email).matches();
    }
    
    public static void validateStringLength(String value, String fieldName, int minLength, int maxLength) {
        validateRequired(value, fieldName);
        int length = value.length();
        if (length < minLength) {
            throw new ValidationException(
                String.format("%s must be at least %d characters long", fieldName, minLength));
        }
        if (length > maxLength) {
            throw new ValidationException(
                String.format("%s must not exceed %d characters", fieldName, maxLength));
        }
    }
    
    public static void validatePositive(Number value, String fieldName) {
        validateRequired(value, fieldName);
        if (value.doubleValue() <= 0) {
            throw new ValidationException(String.format("%s must be positive", fieldName));
        }
    }
}
```

#### Generated Tests
```java
// .ark_output/v_20260112_160000/tests/UserServiceTest.java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void testFindById_Success() {
        // Given
        Long userId = 1L;
        User expectedUser = createTestUser();
        when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));
        
        // When
        Optional<User> result = userService.findById(userId);
        
        // Then
        assertTrue(result.isPresent());
        assertEquals(expectedUser, result.get());
        verify(userRepository).findById(userId);
    }
    
    @Test
    void testFindById_NullId_ThrowsValidationException() {
        // When & Then
        assertThrows(ValidationException.class, () -> userService.findById(null));
    }
    
    @Test
    void testSave_ValidUser_Success() {
        // Given
        User user = createTestUser();
        when(userRepository.save(user)).thenReturn(user);
        
        // When
        User result = userService.save(user);
        
        // Then
        assertEquals(user, result);
        verify(userRepository).save(user);
    }
    
    @Test
    void testSave_InvalidEmail_ThrowsValidationException() {
        // Given
        User user = createTestUser();
        user.setEmail("invalid-email");
        
        // When & Then
        assertThrows(ValidationException.class, () -> userService.save(user));
    }
    
    private User createTestUser() {
        User user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        user.setFirstName("Test");
        user.setLastName("User");
        return user;
    }
}
```

### Results Achieved
- **Code Reduction**: 12,847 lines → 7,234 lines (44% reduction)
- **Consistency**: All services follow same patterns
- **Error Handling**: Comprehensive, consistent exception handling
- **Validation**: Centralized validation with proper error messages
- **Transaction Management**: Proper @Transactional usage
- **Security**: SQL injection risks eliminated
- **Test Coverage**: Generated tests for all consolidated code

---

## 4. Enterprise API Gateway Optimization

### Scenario
Your API gateway has grown to handle 500+ endpoints with duplicated middleware, authentication logic, and route handlers.

### Before Structure
```javascript
routes/
├── user/
│   ├── userRoutes.js             # 234 lines, custom auth middleware
│   ├── userValidation.js         # 123 lines
│   └── userController.js         # 345 lines
├── product/
│   ├── productRoutes.js          # 267 lines, similar auth (85% duplicate)
│   ├── productValidation.js      # 134 lines (70% similar validation patterns)
│   └── productController.js      # 298 lines
├── order/
│   ├── orderRoutes.js            # 298 lines, similar patterns
│   ├── orderValidation.js        # 156 lines
│   └── orderController.js        # 423 lines
└── middleware/
    ├── authMiddleware.js         # 156 lines
    ├── userAuth.js               # 123 lines (80% duplicate)
    ├── jwtAuth.js                # 134 lines (75% duplicate)
    └── validation/
        ├── userValidator.js      # 89 lines
        ├── productValidator.js   # 92 lines (similar patterns)
        └── orderValidator.js     # 87 lines (similar patterns)
```

### ARK-TOOLS Workflow

```bash
/ark-analyze directory=./routes type=comprehensive languages=javascript,typescript
```

#### Analysis Results
```
🔍 API Gateway Analysis
=======================
📂 Discovery: 89 JavaScript files, 15,234 total lines
🔧 Route Analysis: 523 endpoints identified

🎯 Middleware Patterns:
   • Authentication: 47 implementations (12 unique patterns)
   • Validation: 156 validators (23 unique patterns)
   • Error handling: 89 handlers (6 unique patterns)
   • Logging: 67 loggers (inconsistent formats)
   • Rate limiting: 34 implementations (8 different strategies)

🔍 Route Patterns:
   • CRUD operations: 234 routes (highly similar structure)
   • Search endpoints: 45 routes (duplicate pagination logic)
   • File upload: 23 routes (inconsistent handling)
   • Batch operations: 12 routes (similar patterns)

💡 Optimization Opportunities:
   1. Unified authentication middleware
   2. Generic CRUD route generators
   3. Centralized validation framework
   4. Consistent error response format
   5. Standardized logging middleware
```

#### Generated Optimized Gateway
```javascript
// .ark_output/v_20260112_170000/middleware/auth.js
const jwt = require('jsonwebtoken');
const { AuthenticationError, AuthorizationError } = require('../utils/errors');

class UnifiedAuthMiddleware {
  constructor(config = {}) {
    this.jwtSecret = config.jwtSecret || process.env.JWT_SECRET;
    this.tokenHeader = config.tokenHeader || 'authorization';
    this.skipPaths = config.skipPaths || [];
    this.requiredRoles = config.requiredRoles || [];
  }

  authenticate() {
    return async (req, res, next) => {
      try {
        // Skip authentication for whitelisted paths
        if (this.skipPaths.some(path => req.path.startsWith(path))) {
          return next();
        }

        const token = this.extractToken(req);
        if (!token) {
          throw new AuthenticationError('Authentication token required');
        }

        const decoded = jwt.verify(token, this.jwtSecret);
        req.user = decoded;

        // Check required roles if specified
        if (this.requiredRoles.length > 0) {
          this.checkRoles(decoded.roles || []);
        }

        next();
      } catch (error) {
        if (error.name === 'JsonWebTokenError') {
          return next(new AuthenticationError('Invalid authentication token'));
        }
        if (error.name === 'TokenExpiredError') {
          return next(new AuthenticationError('Authentication token expired'));
        }
        next(error);
      }
    };
  }

  requireRoles(...roles) {
    return (req, res, next) => {
      try {
        if (!req.user) {
          throw new AuthenticationError('Authentication required');
        }

        const userRoles = req.user.roles || [];
        const hasRequiredRole = roles.some(role => userRoles.includes(role));

        if (!hasRequiredRole) {
          throw new AuthorizationError('Insufficient permissions');
        }

        next();
      } catch (error) {
        next(error);
      }
    };
  }

  extractToken(req) {
    const authHeader = req.get(this.tokenHeader);
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
    return req.query.token || req.body.token;
  }

  checkRoles(userRoles) {
    const hasRequiredRole = this.requiredRoles.some(role => userRoles.includes(role));
    if (!hasRequiredRole) {
      throw new AuthorizationError('Insufficient permissions');
    }
  }
}

module.exports = UnifiedAuthMiddleware;

// .ark_output/v_20260112_170000/routes/genericCrudRoutes.js
const express = require('express');
const { ValidationError } = require('../utils/errors');

class GenericCrudRoutes {
  constructor(options) {
    this.model = options.model;
    this.modelName = options.modelName;
    this.validation = options.validation || {};
    this.permissions = options.permissions || {};
    this.middleware = options.middleware || [];
    this.router = express.Router();
    
    this.setupRoutes();
  }

  setupRoutes() {
    // GET /{resource} - List with pagination
    this.router.get('/', 
      ...this.middleware,
      this.validateQuery(),
      this.handleList()
    );

    // GET /{resource}/:id - Get by ID
    this.router.get('/:id',
      ...this.middleware,
      this.validateParams(),
      this.handleGetById()
    );

    // POST /{resource} - Create new
    this.router.post('/',
      ...this.middleware,
      this.validateBody('create'),
      this.handleCreate()
    );

    // PUT /{resource}/:id - Update
    this.router.put('/:id',
      ...this.middleware,
      this.validateParams(),
      this.validateBody('update'),
      this.handleUpdate()
    );

    // DELETE /{resource}/:id - Delete
    this.router.delete('/:id',
      ...this.middleware,
      this.validateParams(),
      this.handleDelete()
    );
  }

  validateQuery() {
    return (req, res, next) => {
      const { page = 1, limit = 10, sort = 'id' } = req.query;
      
      req.pagination = {
        page: Math.max(1, parseInt(page)),
        limit: Math.min(100, Math.max(1, parseInt(limit))),
        sort: sort
      };

      next();
    };
  }

  validateParams() {
    return (req, res, next) => {
      const { id } = req.params;
      
      if (!id || !Number.isInteger(Number(id))) {
        return next(new ValidationError('Valid ID required'));
      }

      req.resourceId = parseInt(id);
      next();
    };
  }

  validateBody(operation) {
    return (req, res, next) => {
      try {
        const validator = this.validation[operation];
        if (validator) {
          const { error, value } = validator.validate(req.body);
          if (error) {
            throw new ValidationError(error.details[0].message);
          }
          req.validatedBody = value;
        }
        next();
      } catch (error) {
        next(error);
      }
    };
  }

  handleList() {
    return async (req, res, next) => {
      try {
        const { page, limit, sort } = req.pagination;
        const offset = (page - 1) * limit;

        const [items, total] = await Promise.all([
          this.model.findMany({
            offset,
            limit,
            orderBy: sort
          }),
          this.model.count()
        ]);

        res.json({
          data: items,
          pagination: {
            page,
            limit,
            total,
            totalPages: Math.ceil(total / limit)
          }
        });
      } catch (error) {
        next(error);
      }
    };
  }

  handleGetById() {
    return async (req, res, next) => {
      try {
        const item = await this.model.findById(req.resourceId);
        
        if (!item) {
          return res.status(404).json({
            error: `${this.modelName} not found`
          });
        }

        res.json({ data: item });
      } catch (error) {
        next(error);
      }
    };
  }

  handleCreate() {
    return async (req, res, next) => {
      try {
        const item = await this.model.create(req.validatedBody || req.body);
        res.status(201).json({ data: item });
      } catch (error) {
        next(error);
      }
    };
  }

  // ... other CRUD handlers
}

module.exports = GenericCrudRoutes;

// .ark_output/v_20260112_170000/routes/userRoutes.js (simplified)
const GenericCrudRoutes = require('./genericCrudRoutes');
const UnifiedAuthMiddleware = require('../middleware/auth');
const User = require('../models/User');
const userValidation = require('../validation/userValidation');

const auth = new UnifiedAuthMiddleware();

const userRoutes = new GenericCrudRoutes({
  model: User,
  modelName: 'User',
  validation: userValidation,
  middleware: [
    auth.authenticate(),
    auth.requireRoles('user', 'admin')
  ]
});

// Add user-specific routes
userRoutes.router.get('/me', 
  auth.authenticate(),
  async (req, res, next) => {
    try {
      const user = await User.findById(req.user.id);
      res.json({ data: user });
    } catch (error) {
      next(error);
    }
  }
);

module.exports = userRoutes.router;
```

### Results Achieved
- **Code Reduction**: 15,234 lines → 8,567 lines (44% reduction)
- **Route Generation**: Generic CRUD routes for 90% of endpoints
- **Middleware Consolidation**: 47 auth implementations → 1 unified
- **Consistency**: Standardized error handling and response formats
- **Performance**: 23% faster response times due to optimized middleware
- **Maintainability**: Single source of truth for common patterns

---

## 5. DevOps Script Consolidation

### Scenario
Your DevOps team has 200+ deployment, monitoring, and utility scripts with significant duplication and inconsistent error handling.

### Before Structure
```bash
scripts/
├── deployment/
│   ├── deploy-api.sh             # 234 lines
│   ├── deploy-frontend.sh        # 198 lines (70% similar)
│   ├── deploy-workers.sh         # 267 lines (65% similar)
│   └── rollback-api.sh           # 123 lines
├── monitoring/
│   ├── check-api-health.sh       # 89 lines
│   ├── check-db-health.sh        # 92 lines (80% similar)
│   ├── check-redis-health.sh     # 87 lines (85% similar)
│   └── alert-on-failure.sh       # 156 lines
├── backup/
│   ├── backup-database.sh        # 178 lines
│   ├── backup-files.sh           # 145 lines (60% similar structure)
│   └── cleanup-old-backups.sh    # 123 lines
└── utils/
    ├── log-helper.sh             # 67 lines
    ├── logging-utils.sh          # 72 lines (95% duplicate)
    ├── error-handler.sh          # 45 lines
    └── common-functions.sh       # 234 lines
```

### ARK-TOOLS Workflow

```bash
/ark-analyze directory=./scripts type=comprehensive languages=bash,shell
```

#### Generated Consolidated Scripts
```bash
#!/bin/bash
# .ark_output/v_20260112_180000/lib/common.sh
# Unified DevOps utility library

set -euo pipefail

# Global configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-/var/log/devops.log}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"
DRY_RUN="${DRY_RUN:-false}"

# Logging functions
log_info() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] INFO: $message" | tee -a "$LOG_FILE"
}

log_error() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ERROR: $message" >&2 | tee -a "$LOG_FILE"
}

log_warning() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] WARN: $message" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    local exit_code=$1
    local line_number=$2
    local command="$3"
    
    log_error "Command failed with exit code $exit_code at line $line_number: $command"
    
    if [[ -n "$ALERT_WEBHOOK" ]]; then
        send_alert "Script Error" "Command '$command' failed at line $line_number"
    fi
    
    cleanup_on_error
    exit $exit_code
}

# Set error trap
trap 'handle_error $? $LINENO "$BASH_COMMAND"' ERR

# Health check utilities
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    local timeout="${3:-30}"
    local max_retries="${4:-3}"
    
    log_info "Checking health of $service_name at $health_url"
    
    for ((i=1; i<=max_retries; i++)); do
        if curl -sSf --max-time "$timeout" "$health_url" >/dev/null 2>&1; then
            log_info "$service_name is healthy (attempt $i/$max_retries)"
            return 0
        else
            log_warning "$service_name health check failed (attempt $i/$max_retries)"
            if [[ $i -lt $max_retries ]]; then
                sleep $((i * 2))  # Exponential backoff
            fi
        fi
    done
    
    log_error "$service_name is unhealthy after $max_retries attempts"
    return 1
}

# Database utilities
check_database_connection() {
    local db_host="$1"
    local db_port="$2"
    local db_name="$3"
    local db_user="$4"
    
    log_info "Testing database connection to $db_host:$db_port/$db_name"
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -c "SELECT 1;" >/dev/null 2>&1; then
        log_info "Database connection successful"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

# Deployment utilities
deploy_service() {
    local service_name="$1"
    local image_tag="$2"
    local config_file="$3"
    local health_endpoint="$4"
    
    log_info "Starting deployment of $service_name:$image_tag"
    
    # Validate parameters
    [[ -z "$service_name" ]] && { log_error "Service name required"; return 1; }
    [[ -z "$image_tag" ]] && { log_error "Image tag required"; return 1; }
    [[ ! -f "$config_file" ]] && { log_error "Config file not found: $config_file"; return 1; }
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would deploy $service_name:$image_tag"
        return 0
    fi
    
    # Blue-green deployment
    local current_color=$(get_current_deployment_color "$service_name")
    local new_color=$([[ "$current_color" == "blue" ]] && echo "green" || echo "blue")
    
    log_info "Current deployment: $current_color, deploying to: $new_color"
    
    # Deploy to new color
    if deploy_to_color "$service_name" "$image_tag" "$new_color" "$config_file"; then
        log_info "Deployment to $new_color successful"
        
        # Health check
        if check_service_health "$service_name-$new_color" "$health_endpoint" 30 5; then
            log_info "Health check passed, switching traffic"
            
            # Switch traffic
            if switch_traffic "$service_name" "$new_color"; then
                log_info "Traffic switched successfully"
                
                # Cleanup old deployment
                cleanup_old_deployment "$service_name" "$current_color"
                
                send_alert "Deployment Success" "$service_name:$image_tag deployed successfully"
                return 0
            else
                log_error "Failed to switch traffic, rolling back"
                rollback_deployment "$service_name" "$current_color"
                return 1
            fi
        else
            log_error "Health check failed, rolling back"
            cleanup_deployment "$service_name" "$new_color"
            return 1
        fi
    else
        log_error "Deployment failed"
        return 1
    fi
}

# Backup utilities
create_backup() {
    local backup_type="$1"
    local source_path="$2"
    local backup_name="${3:-$(date +%Y%m%d_%H%M%S)}"
    
    log_info "Creating $backup_type backup: $backup_name"
    
    case "$backup_type" in
        "database")
            create_database_backup "$source_path" "$backup_name"
            ;;
        "files")
            create_file_backup "$source_path" "$backup_name"
            ;;
        *)
            log_error "Unknown backup type: $backup_type"
            return 1
            ;;
    esac
}

# Alert utilities
send_alert() {
    local title="$1"
    local message="$2"
    local severity="${3:-info}"
    
    if [[ -n "$ALERT_WEBHOOK" ]]; then
        local payload=$(cat <<EOF
{
    "title": "$title",
    "message": "$message",
    "severity": "$severity",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)"
}
EOF
)
        
        curl -sSf -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$ALERT_WEBHOOK" || log_warning "Failed to send alert"
    else
        log_info "ALERT: $title - $message"
    fi
}

#!/bin/bash
# .ark_output/v_20260112_180000/scripts/deploy.sh
# Unified deployment script

source "$(dirname "$0")/../lib/common.sh"

# Configuration
SERVICE_NAME="${1:-}"
IMAGE_TAG="${2:-latest}"
ENVIRONMENT="${3:-staging}"
CONFIG_DIR="${SCRIPT_DIR}/../config"

usage() {
    cat <<EOF
Usage: $0 <service> <tag> [environment]

Arguments:
    service      Service to deploy (api|frontend|workers)
    tag          Image tag to deploy
    environment  Target environment (staging|production)

Environment Variables:
    DRY_RUN=true     Preview deployment without executing
    FORCE=true       Skip confirmations
    ALERT_WEBHOOK    Webhook URL for notifications

Examples:
    $0 api v1.2.3 production
    DRY_RUN=true $0 frontend latest staging
EOF
    exit 1
}

main() {
    [[ -z "$SERVICE_NAME" ]] && usage
    
    log_info "Starting deployment process"
    log_info "Service: $SERVICE_NAME"
    log_info "Tag: $IMAGE_TAG"
    log_info "Environment: $ENVIRONMENT"
    
    # Validate inputs
    case "$SERVICE_NAME" in
        api|frontend|workers)
            ;;
        *)
            log_error "Invalid service: $SERVICE_NAME"
            exit 1
            ;;
    esac
    
    # Load environment-specific configuration
    local config_file="$CONFIG_DIR/$ENVIRONMENT/$SERVICE_NAME.env"
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    source "$config_file"
    
    # Pre-deployment checks
    log_info "Running pre-deployment checks"
    
    # Check if image exists
    if ! docker image inspect "$SERVICE_NAME:$IMAGE_TAG" >/dev/null 2>&1; then
        log_error "Image not found: $SERVICE_NAME:$IMAGE_TAG"
        exit 1
    fi
    
    # Check database connectivity
    if [[ "$SERVICE_NAME" == "api" ]]; then
        check_database_connection "$DB_HOST" "$DB_PORT" "$DB_NAME" "$DB_USER" || exit 1
    fi
    
    # Confirmation for production
    if [[ "$ENVIRONMENT" == "production" && "$FORCE" != "true" ]]; then
        read -p "Deploy $SERVICE_NAME:$IMAGE_TAG to PRODUCTION? [y/N] " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && { log_info "Deployment cancelled"; exit 0; }
    fi
    
    # Perform deployment
    local health_endpoint="$HEALTH_URL"
    if deploy_service "$SERVICE_NAME" "$IMAGE_TAG" "$config_file" "$health_endpoint"; then
        log_info "Deployment completed successfully"
        
        # Post-deployment checks
        log_info "Running post-deployment verification"
        
        # Run smoke tests if available
        local smoke_test_script="$SCRIPT_DIR/smoke-tests/$SERVICE_NAME.sh"
        if [[ -f "$smoke_test_script" ]]; then
            log_info "Running smoke tests"
            bash "$smoke_test_script" || log_warning "Some smoke tests failed"
        fi
        
        exit 0
    else
        log_error "Deployment failed"
        exit 1
    fi
}

main "$@"
```

### Generated Testing Framework
```bash
#!/bin/bash
# .ark_output/v_20260112_180000/tests/test_runner.sh
# Comprehensive test runner for DevOps scripts

source "$(dirname "$0")/../lib/common.sh"

# Test framework
test_count=0
test_passed=0
test_failed=0

assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    ((test_count++))
    
    if [[ "$expected" == "$actual" ]]; then
        log_info "✓ $test_name"
        ((test_passed++))
    else
        log_error "✗ $test_name"
        log_error "  Expected: $expected"
        log_error "  Actual: $actual"
        ((test_failed++))
    fi
}

assert_success() {
    local command="$1"
    local test_name="$2"
    
    ((test_count++))
    
    if eval "$command" >/dev/null 2>&1; then
        log_info "✓ $test_name"
        ((test_passed++))
    else
        log_error "✗ $test_name"
        log_error "  Command failed: $command"
        ((test_failed++))
    fi
}

# Tests
test_logging_functions() {
    log_info "Testing logging functions"
    
    assert_success "log_info 'test message'" "log_info function works"
    assert_success "log_warning 'test warning'" "log_warning function works"
    assert_success "log_error 'test error'" "log_error function works"
}

test_deployment_functions() {
    log_info "Testing deployment functions"
    
    # Mock deployment
    DRY_RUN=true
    assert_success "deploy_service 'test-service' 'v1.0.0' '/dev/null' 'http://localhost'" "deploy_service dry run works"
}

run_all_tests() {
    log_info "Starting DevOps script tests"
    
    test_logging_functions
    test_deployment_functions
    
    log_info "Tests completed: $test_count total, $test_passed passed, $test_failed failed"
    
    if [[ $test_failed -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

run_all_tests
```

### Results Achieved
- **Script Reduction**: 200+ scripts → 12 unified tools
- **Code Reduction**: 8,765 lines → 2,234 lines (74% reduction)
- **Consistency**: Standardized error handling, logging, and patterns
- **Reliability**: Comprehensive error handling and rollback mechanisms
- **Testing**: Complete test coverage for all consolidated functions
- **Documentation**: Self-documenting code with usage examples

---

## 🎉 Summary

These examples demonstrate ARK-TOOLS' power across different scenarios:

- **Python Microservices**: 50% code reduction, unified patterns
- **React Components**: 48% reduction, consistent design system
- **Java Enterprise**: 44% reduction, modern patterns, security fixes
- **API Gateway**: 44% reduction, standardized middleware
- **DevOps Scripts**: 74% reduction, reliable automation

### Common Benefits Achieved

1. **Massive Code Reduction**: 40-75% reduction in duplicate code
2. **Quality Improvement**: Comprehensive error handling, type safety, testing
3. **Consistency**: Unified patterns and standards across codebases
4. **Maintainability**: Single source of truth for common functionality
5. **Safety**: Zero original file modifications, complete rollback capability
6. **Documentation**: Self-documenting consolidated code with examples

### Key Success Factors

- **Start Conservative**: Use conservative strategy for first transformations
- **Validate Everything**: Run generated tests before integration
- **Review Before Using**: Always examine consolidated code
- **Gradual Integration**: Integrate consolidated code incrementally
- **Monitor Results**: Track metrics after consolidation

Ready to try ARK-TOOLS on your codebase? Start with the [Quick Start Guide](QUICK_START_GUIDE.md)!