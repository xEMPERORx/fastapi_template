# Graph Report - fastapi_template  (2026-07-16)

## Corpus Check
- 114 files · ~27,847 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 955 nodes · 1670 edges · 69 communities (53 shown, 16 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 299 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `55ee4f89`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]

## God Nodes (most connected - your core abstractions)
1. `cn()` - 102 edges
2. `RoleRepository` - 29 edges
3. `UserRepository` - 28 edges
4. `RoleService` - 27 edges
5. `UserManagementService` - 24 edges
6. `Architecture` - 18 edges
7. `RetryConfig` - 16 edges
8. `UserNotFound` - 16 edges
9. `PermissionRepository` - 16 edges
10. `LoggedService` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Skill Plugin Architecture` --semantically_similar_to--> `Dependency Injection Pattern`  [INFERRED] [semantically similar]
  fastapi_skill_plan.md → CLAUDE.md
- `Fault-Tolerance Recovery Patterns` --semantically_similar_to--> `Skill Lifecycle Management`  [INFERRED] [semantically similar]
  CLAUDE.md → fastapi_skill_plan.md
- `get_logout_service()` --calls--> `LogoutUser`  [INFERRED]
  app/core/dependency_factory.py → C:/Users/patel/Downloads/fastapi_template-main/fastapi_template-main/app/services/auth/logout.py
- `get_verify_mail_service()` --calls--> `VerifyMail`  [INFERRED]
  app/core/dependency_factory.py → C:/Users/patel/Downloads/fastapi_template-main/fastapi_template-main/app/services/verify/mail_verify.py
- `LogoutUser` --uses--> `LoggedService`  [INFERRED]
  C:/Users/patel/Downloads/fastapi_template-main/fastapi_template-main/app/services/auth/logout.py → app/core/logger.py

## Hyperedges (group relationships)
- **Authentication Subsystem** — claude_md_dual_token_auth, claude_md_rbac_authorization, claude_md_input_validation, claude_md_security_headers [EXTRACTED 1.00]
- **Infrastructure Stack** — docker_compose_postgres, docker_compose_redis, docker_compose_elasticsearch, docker_compose_kibana [EXTRACTED 1.00]
- **Observability Pattern** — claude_md_structured_logging, claude_md_health_checks, claude_md_error_handling, docker_compose_kibana [INFERRED 0.85]

## Communities (69 total, 16 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (88): PageHeader(), apiErrorMessage(), authApi, permissionsApi, rolesApi, usersApi, cn(), RoleManageDialog() (+80 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (37): ProtectedRoute(), AppLayout(), NAV_ITEMS, api, original, RetriableConfig, AuthState, useAuthStore (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (22): LogoutUser, get_login_service(), get_logout_service(), get_permission_repository(), get_permission_service(), get_role_repository(), get_role_service(), get_search_repository() (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (19): pagination_dependency(), PaginationParams, Advanced input validation and sanitization utilities.  Provides: - Pydantic fiel, HTML-encode a string so tags are rendered inert., Strip common XSS and SQL-injection signatures from a plain-text field., Convert any value to a safe string, stripping HTML and injection markers., safe_str(), sanitize_text() (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (30): GoogleOAuthService, Refresh, BaseModel, get_google_oauth_service(), Reduce a value to a safe identifier (e.g. a username derived from an email)., sanitize_identifier(), GoogleAuthUrlResponse, GoogleOAuthCallbackResponse (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (16): Fetch a user with roles, role permissions, and direct permissions eagerly loaded, UserRepository, Base, Bootstrap script for a fresh deployment.  The hierarchical RBAC model has a chic, seed(), get_verify_mail_service(), Base, get_db() (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (35): Architecture, Authentication Flow, Background Tasks, Celery Worker, Claude Code Skills, code:bash (# Install dependencies), code:bash (# Run all tests), code:bash (# Start all services) (+27 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (17): ResetPassword, get_reset_password_service(), async_retry(), CircuitBreaker, CircuitBreakerConfig, CircuitOpenError, Advanced error recovery utilities.  Provides: - Retry with exponential backoff a, Thread-safe-ish circuit breaker for async external calls. (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (14): Data validation and integrity utilities.  Provides: - Data integrity checks for, Strip path-traversal and dangerous chars, return safe filename., Validate and coerce raw dict data against a Pydantic model., Raise ValueError if any required key is missing or empty., Recursively trim overly-long strings in a dict., safe_filename(), sanitize_dict(), validate_model_fields() (+6 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (17): BeautifulFormatter, _infer_layer(), log_function(), log_method(), LoggedMethods, LoggedRepository, LoggedService, Central logging utilities for the FastAPI starter template.  Features: - Request (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.19
Nodes (7): PermissionAlreadyGranted, PermissionNotFound, PermissionNotGranted, RBACException, RoleExists, RoleNotFound, RoleService

### Community 12 - "Community 12"
Cohesion: 0.1
Nodes (22): override_permission_dependencies(), Scenario: assign role to the user, Scenario: Test role list, Scenario: Test role list, Scenario: Register and get user id, Scenario: Register, log in, and return (user_id, access_token)., Scenario: create and get permission, Scenario: Register and get user id (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (18): check_db(), check_elasticsearch(), check_redis(), HealthReport, HealthStatus, Automated health-check logic.  Provides status checks for: - Database connectivi, Run all registered health checks and aggregate the result., Run all registered health checks and aggregate the result. (+10 more)

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (14): LoginUser, RegisterUser, get_register_service(), AppException, RateLimit, Base class for all custom application errors., UserException, UserMailExist (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (10): can_grant_permission(), can_grant_role(), effective_permissions(), Delegated-authorization helpers for the hierarchical RBAC model.  A user's permi, Union of a user's role-derived permissions and direct permission grants.      Re, GrantNotAllowed, RoleAlreadyAssigned, RoleNotAssigned (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (8): FixedWindowLimiter, No-op: state lives in Redis, not this process. Provided so callers         (e.g., Get remaining requests in current window, Get remaining requests in current window, Fixed window rate limiter, Fixed-window rate limiter backed by Redis (INCR + EXPIRE), correct     across mu, In-process fixed window rate limiter.      Only correct for a single worker/proc, RedisFixedWindowLimiter

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (16): mock_get_current_user(), MockUser, Test: Registering User, Test: Sending an invalid email and a short password, Test POST /api/v1/auth/login using Form Data, Test GET /api/v1/auth/user with Dependency Injection, Scenario: User provides NO token at all, Scenario: User provides a 'junk' token (+8 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (16): Authentication Flow, code:python (from app.core.data_validation import safe_filename, validate), code:python (from app.core.recovery import async_retry, RetryConfig), code:python (from app.core.recovery import CircuitBreaker, CircuitBreaker), code:json ({), code:python (limiter = FixedWindowLimiter(requests=10, window_seconds=60)), code:json ({), code:python (from app.core.dependencies import role_required, permission_) (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (14): get_current_user_info(), login_user(), logout_user(), Get the currently authenticated user's information., Register a new user account., Verify the mail via token, Authenticate a user and return a JWT access token., Implement the Logout Functionality (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (14): FastAPI Layered Architecture Guide, Celery Background Tasks, Dependency Injection Pattern, Kubernetes Health Check Endpoints, FastAPI API Container, Celery Worker Container, PostgreSQL Database Container, Docker Compose Full Stack (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (12): Available API Areas, code:block1 (middleware -> route -> service -> repository -> db/external ), code:bash (docker compose up --build), code:bash (pytest                                    # all tests), Docker Setup, Extending This Template, FastAPI Template, Notes for Reuse (+4 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (6): assign_role_to_user(), get_my_grants(), grant_permission_to_user(), What the logged-in user may grant to others: their effective permissions     plu, Assign a role to a user. Only allowed if one of the caller's own roles     is co, Grant a single permission directly to a user, bypassing roles entirely.     Only

### Community 25 - "Community 25"
Cohesion: 0.2
Nodes (9): create_exception_handler(), create_global_handler(), Factory to create the global handler exception, A factory that creates handlers for custom exceptions., Factory to create the global handler exception, A factory that creates handlers for custom exceptions., Register all custom exception handlers for the application., Register all custom exception handlers for the application. (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.29
Nodes (6): AppException, Custom exceptions for input validation errors., Raised when input sanitization fails., Base class for all validation-related errors., SanitizationError, ValidationError

### Community 27 - "Community 27"
Cohesion: 0.4
Nodes (9): make_superuser(), Tests for the hierarchical / delegated RBAC model: superuser bootstrap, direct p, Simulate what the seed script does: no API path can do this — is_superuser     i, register_and_login(), test_direct_permission_grant_and_revoke(), test_grant_role_requires_delegation(), test_me_grants_reflects_superuser(), test_non_superuser_without_permission_is_forbidden() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.28
Nodes (4): get_current_user(), Extract and verify the bearer token from the Authorization header., Verify, InvalidToken

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (7): do_run_migrations(), Run migrations in 'offline' mode.      This configures the context with just a U, In this scenario we need to create an Engine     and associate a connection with, Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 30 - "Community 30"
Cohesion: 0.43
Nodes (6): Tests for security middleware and validation integration., test_health_endpoint_returns_valid_response(), test_liveness_probe(), test_security_headers_present(), TestHealthEndpoints, TestSecurityHeaders

### Community 31 - "Community 31"
Cohesion: 0.48
Nodes (5): create_new_permission(), delete_permission_endpoint(), read_permission(), read_permissions(), update_permission_endpoint()

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (4): grant_permission_required(), grant_role_required(), Gate an endpoint that assigns a `role_id` path param to a user, based on     the, Gate an endpoint that grants a `permission_id` path param directly to a user.

### Community 33 - "Community 33"
Cohesion: 0.29
Nodes (4): cleanup_expired_tokens(), Periodic housekeeping: refresh tokens accumulate forever otherwise., send_email_bg(), create_message()

### Community 34 - "Community 34"
Cohesion: 0.29
Nodes (7): API server, Celery beat (scheduled tasks), Celery worker, code:bash (uvicorn app.main:app --reload), code:bash (python -m celery -A app.queue.celery worker --loglevel=info), code:bash (python -m celery -A app.queue.celery beat --loglevel=info), Run Locally

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (7): 1. Create environment variables, 2. Install dependencies, 3. Run database migrations, code:bash (cp .env.example .env), code:bash (pip install -r requirements.txt), code:bash (alembic upgrade head), Local Setup

### Community 38 - "Community 38"
Cohesion: 0.5
Nodes (3): Security middleware: security headers enforcement and request body sanitization., Register middleware that adds security headers to every response., register_security_middleware()

### Community 39 - "Community 39"
Cohesion: 0.6
Nodes (3): downgrade(), create initial tables  Revision ID: 10328bfc2473 Revises: Create Date: 2026-04-0, upgrade()

### Community 40 - "Community 40"
Cohesion: 0.4
Nodes (4): code:json ({), Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 43 - "Community 43"
Cohesion: 0.5
Nodes (3): Register rate limiting middleware., Register rate limiting middleware., register_ratelimit_middleware()

### Community 46 - "Community 46"
Cohesion: 0.5
Nodes (4): code:python (from app.core.validation import SafeStr, SafeEmail, StrongPa), code:python (from app.core.validation import sanitize_text, strip_html, s), code:python (from app.core.validation import PaginationParams, StrictPagi), Input Validation & Sanitization

### Community 50 - "Community 50"
Cohesion: 0.67
Nodes (3): code:python (from app.core.logger import log_function, LoggedService, Log), code:python (from app.core.logger import log_info, log_warning, log_debug), Structured Logging

### Community 51 - "Community 51"
Cohesion: 0.67
Nodes (3): Centralized Error Handling, Structured Logging with Request ID, Kibana Container

## Knowledge Gaps
- **173 isolated node(s):** `Register a new user account.`, `Verify the mail via token`, `Authenticate a user and return a JWT access token.`, `Implement the Logout Functionality`, `Use Refresh Token To get new access Token and refresh Token.` (+168 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserRepository` connect `Community 5` to `Community 2`, `Community 4`, `Community 37`, `Community 7`, `Community 9`, `Community 14`, `Community 15`, `Community 28`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `seed()` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `Input()` connect `Community 0` to `Community 5`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `RoleRepository` (e.g. with `LoggedRepository` and `RoleCreate`) actually correct?**
  _`RoleRepository` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `UserRepository` (e.g. with `LoggedRepository` and `GoogleOAuthService`) actually correct?**
  _`UserRepository` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `RoleService` (e.g. with `LoggedService` and `PermissionAlreadyGranted`) actually correct?**
  _`RoleService` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `UserManagementService` (e.g. with `LoggedService` and `GrantNotAllowed`) actually correct?**
  _`UserManagementService` has 13 INFERRED edges - model-reasoned connections that need verification._