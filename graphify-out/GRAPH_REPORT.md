# Graph Report - .  (2026-05-09)

## Corpus Check
- 70 files · ~13,206 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 518 nodes · 709 edges · 45 communities (33 shown, 12 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 177 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Error Handling & Auth|Error Handling & Auth]]
- [[_COMMUNITY_Input Validation & Sanitization|Input Validation & Sanitization]]
- [[_COMMUNITY_Auth Routes & OAuth|Auth Routes & OAuth]]
- [[_COMMUNITY_Structured Logging System|Structured Logging System]]
- [[_COMMUNITY_Data Validation & Integrity|Data Validation & Integrity]]
- [[_COMMUNITY_RBAC Roles Management|RBAC Roles Management]]
- [[_COMMUNITY_Dependency Injection Factory|Dependency Injection Factory]]
- [[_COMMUNITY_Fault Tolerance & Recovery|Fault Tolerance & Recovery]]
- [[_COMMUNITY_RBAC Permissions Management|RBAC Permissions Management]]
- [[_COMMUNITY_Health Check System|Health Check System]]
- [[_COMMUNITY_ES Client & Search|ES Client & Search]]
- [[_COMMUNITY_Security Middleware|Security Middleware]]
- [[_COMMUNITY_Database Session Management|Database Session Management]]
- [[_COMMUNITY_Rate Limiting Middleware|Rate Limiting Middleware]]
- [[_COMMUNITY_Email Verification & SMTP|Email Verification & SMTP]]
- [[_COMMUNITY_Application Settings Config|Application Settings Config]]
- [[_COMMUNITY_Celery Queue & Tasks|Celery Queue & Tasks]]
- [[_COMMUNITY_Main App Entry Point|Main App Entry Point]]
- [[_COMMUNITY_RBAC Database Models|RBAC Database Models]]
- [[_COMMUNITY_Search Schema & Types|Search Schema & Types]]
- [[_COMMUNITY_Permission Schema Types|Permission Schema Types]]
- [[_COMMUNITY_Role Schema Types|Role Schema Types]]
- [[_COMMUNITY_User Schema Types|User Schema Types]]
- [[_COMMUNITY_Docker Infrastructure|Docker Infrastructure]]
- [[_COMMUNITY_Test Permissions & Roles|Test Permissions & Roles]]
- [[_COMMUNITY_Test Validation|Test Validation]]
- [[_COMMUNITY_Test Recovery|Test Recovery]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]
- [[_COMMUNITY_Skill Plugin Architecture|Skill Plugin Architecture]]
- [[_COMMUNITY_Redis Cache Infrastructure|Redis Cache Infrastructure]]
- [[_COMMUNITY_Elasticsearch Container|Elasticsearch Container]]
- [[_COMMUNITY_Kibana Observability|Kibana Observability]]
- [[_COMMUNITY_PostgreSQL Container|PostgreSQL Container]]

## God Nodes (most connected - your core abstractions)
1. `UserRepository` - 20 edges
2. `RoleRepository` - 17 edges
3. `RoleService` - 16 edges
4. `LoggedService` - 14 edges
5. `PermissionRepository` - 13 edges
6. `PermissionService` - 13 edges
7. `RegisterUser` - 12 edges
8. `CircuitBreaker` - 11 edges
9. `PaginationParams` - 11 edges
10. `GoogleOAuthService` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Skill Plugin Architecture` --semantically_similar_to--> `Dependency Injection Pattern`  [INFERRED] [semantically similar]
  fastapi_skill_plan.md → CLAUDE.md
- `Fault-Tolerance Recovery Patterns` --semantically_similar_to--> `Skill Lifecycle Management`  [INFERRED] [semantically similar]
  CLAUDE.md → fastapi_skill_plan.md
- `get_role_repository()` --calls--> `RoleRepository`  [INFERRED]
  app/core/dependency_factory.py → app/repositories/rbac/role.py
- `TestRetry` --uses--> `RetryConfig`  [INFERRED]
  tests/test_recovery.py → app/core/recovery.py
- `TestCircuitBreaker` --uses--> `RetryConfig`  [INFERRED]
  tests/test_recovery.py → app/core/recovery.py

## Hyperedges (group relationships)
- **Authentication Subsystem** — claude_md_dual_token_auth, claude_md_rbac_authorization, claude_md_input_validation, claude_md_security_headers [EXTRACTED 1.00]
- **Infrastructure Stack** — docker_compose_postgres, docker_compose_redis, docker_compose_elasticsearch, docker_compose_kibana [EXTRACTED 1.00]
- **Observability Pattern** — claude_md_structured_logging, claude_md_health_checks, claude_md_error_handling, docker_compose_kibana [INFERRED 0.85]

## Communities (45 total, 12 thin omitted)

### Community 0 - "Error Handling & Auth"
Cohesion: 0.06
Nodes (26): get_current_user(), Extract and verify the bearer token from the Authorization header., LoginUser, RegisterUser, Verify, get_login_service(), get_register_service(), AppException (+18 more)

### Community 1 - "Input Validation & Sanitization"
Cohesion: 0.07
Nodes (19): pagination_dependency(), PaginationParams, Advanced input validation and sanitization utilities.  Provides: - Pydantic fiel, HTML-encode a string so tags are rendered inert., Strip common XSS and SQL-injection signatures from a plain-text field., Convert any value to a safe string, stripping HTML and injection markers., safe_str(), sanitize_text() (+11 more)

### Community 2 - "Auth Routes & OAuth"
Cohesion: 0.07
Nodes (23): GoogleOAuthService, LogoutUser, Refresh, BaseModel, get_google_oauth_service(), get_logout_service(), get_password_reset_service(), get_search_service() (+15 more)

### Community 3 - "Structured Logging System"
Cohesion: 0.08
Nodes (17): BeautifulFormatter, _infer_layer(), log_function(), log_method(), LoggedMethods, LoggedRepository, LoggedService, Central logging utilities for the FastAPI starter template.  Features: - Requ (+9 more)

### Community 4 - "Data Validation & Integrity"
Cohesion: 0.09
Nodes (14): Data validation and integrity utilities.  Provides: - Data integrity checks for, Strip path-traversal and dangerous chars, return safe filename., Validate and coerce raw dict data against a Pydantic model., Raise ValueError if any required key is missing or empty., Recursively trim overly-long strings in a dict., safe_filename(), sanitize_dict(), validate_model_fields() (+6 more)

### Community 5 - "RBAC Roles Management"
Cohesion: 0.09
Nodes (7): get_role_service(), RoleRepository, RoleService, Role, RoleBase, RoleCreate, RoleUpdate

### Community 6 - "Dependency Injection Factory"
Cohesion: 0.07
Nodes (10): ResetPassword, UserRepository, get_reset_password_service(), get_role_repository(), get_search_repository(), get_user_repository(), get_verify_mail_service(), LoggedRepository (+2 more)

### Community 7 - "Fault Tolerance & Recovery"
Cohesion: 0.14
Nodes (14): async_retry(), CircuitBreaker, CircuitBreakerConfig, CircuitOpenError, Advanced error recovery utilities.  Provides: - Retry with exponential backoff a, Thread-safe-ish circuit breaker for async external calls., Raised when a circuit breaker is open and the call is rejected., Call *func* with exponential backoff + optional jitter on retryable errors. (+6 more)

### Community 8 - "RBAC Permissions Management"
Cohesion: 0.11
Nodes (8): get_permission_repository(), get_permission_service(), PermissionService, PermissionRepository, PermissionBase, PermissionCreate, PermissionResponse, PermissionUpdate

### Community 9 - "Health Check System"
Cohesion: 0.15
Nodes (16): check_db(), check_elasticsearch(), check_redis(), HealthReport, HealthStatus, Automated health-check logic.  Provides status checks for: - Database connectivi, Run all registered health checks and aggregate the result., Ping the database with a lightweight query. (+8 more)

### Community 10 - "ES Client & Search"
Cohesion: 0.12
Nodes (16): mock_get_current_user(), MockUser, Test: Registering User, Test: Sending an invalid email and a short password, Test POST /api/v1/auth/login using Form Data, Test GET /api/v1/auth/user with Dependency Injection, Scenario: User provides NO token at all, Scenario: User provides a 'junk' token (+8 more)

### Community 11 - "Security Middleware"
Cohesion: 0.13
Nodes (12): get_current_user_info(), login_user(), logout_user(), Get the currently authenticated user's information., Register a new user account., Verify the mail via token, Authenticate a user and return a JWT access token., Implement the Logout Functionality (+4 more)

### Community 12 - "Database Session Management"
Cohesion: 0.14
Nodes (14): override_permission_dependencies(), Scenario: Test role list, Scenario: Register and get user id, Scenario: create and get permission, Scenario: Test permission list, Scenario: Role create and get role, Bypass RBAC permission guards for non-auth API tests., Scenario: assign role to the user (+6 more)

### Community 13 - "Rate Limiting Middleware"
Cohesion: 0.15
Nodes (14): FastAPI Layered Architecture Guide, Celery Background Tasks, Dependency Injection Pattern, Kubernetes Health Check Endpoints, FastAPI API Container, Celery Worker Container, PostgreSQL Database Container, Docker Compose Full Stack (+6 more)

### Community 14 - "Email Verification & SMTP"
Cohesion: 0.22
Nodes (7): Base, Base, DeclarativeBase, RefreshToken, User, Permission, Role

### Community 16 - "Application Settings Config"
Cohesion: 0.28
Nodes (6): AppException, Custom exceptions for input validation errors., Raised when input sanitization fails., Base class for all validation-related errors., SanitizationError, ValidationError

### Community 17 - "Celery Queue & Tasks"
Cohesion: 0.29
Nodes (6): Run migrations in 'offline' mode.      This configures the context with just a U, In this scenario we need to create an Engine     and associate a connection with, Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 18 - "Main App Entry Point"
Cohesion: 0.29
Nodes (3): FixedWindowLimiter, Get remaining requests in current window, Fixed window rate limiter

### Community 19 - "RBAC Database Models"
Cohesion: 0.29
Nodes (3): Tests for security middleware and validation integration., TestHealthEndpoints, TestSecurityHeaders

### Community 22 - "Permission Schema Types"
Cohesion: 0.5
Nodes (3): Security middleware: security headers enforcement and request body sanitization., Register middleware that adds security headers to every response., register_security_middleware()

### Community 31 - "Test Recovery"
Cohesion: 0.67
Nodes (3): Centralized Error Handling, Structured Logging with Request ID, Kibana Container

## Knowledge Gaps
- **89 isolated node(s):** `Register a new user account.`, `Verify the mail via token`, `Authenticate a user and return a JWT access token.`, `Implement the Logout Functionality`, `Use Refresh Token To get new access Token and refresh Token.` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LoggedService` connect `Structured Logging System` to `Error Handling & Auth`, `Auth Routes & OAuth`, `RBAC Roles Management`, `Dependency Injection Factory`, `RBAC Permissions Management`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `AppException` connect `Error Handling & Auth` to `Application Settings Config`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `UserRepository` connect `Dependency Injection Factory` to `Error Handling & Auth`, `Auth Routes & OAuth`, `Structured Logging System`, `Email Verification & SMTP`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `UserRepository` (e.g. with `LoggedRepository` and `GoogleOAuthService`) actually correct?**
  _`UserRepository` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `RoleRepository` (e.g. with `LoggedRepository` and `RoleCreate`) actually correct?**
  _`RoleRepository` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `RoleService` (e.g. with `LoggedService` and `RoleRepository`) actually correct?**
  _`RoleService` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `LoggedService` (e.g. with `GoogleOAuthService` and `LoginUser`) actually correct?**
  _`LoggedService` has 12 INFERRED edges - model-reasoned connections that need verification._