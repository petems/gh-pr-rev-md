# Git Detection Refactoring Plan

## Current State Analysis

### Existing Functionality
The tool already supports `.` as a shortcut to auto-detect the current branch's PR via `get_current_branch_pr_url()` in `cli.py:26-125`.

### Current Implementation Strengths
- ✅ `.` shortcut works well (`python -m gh_pr_rev_md.cli .`)
- ✅ Comprehensive test coverage (18 test cases in `test_cli.py`)
- ✅ Good error handling with clear messages
- ✅ Supports both SSH and HTTPS remote URLs
- ✅ Fallback chain: GitHub API → GitHub CLI → error
- ✅ Has `find_pr_by_branch` method in GitHubClient

### Issues Identified
1. **Performance**: Uses 3-4 subprocess calls per invocation (~100-200ms overhead)
2. **Dependencies**: Relies on external `git` binary and optionally `gh` CLI
3. **Limited scope**: Only handles 'origin' remote
4. **No GitHub Enterprise**: Hardcoded to github.com only
5. **Code organization**: 100-line monolithic function with mixed concerns
6. **Edge cases**: Missing worktree, multiple remote support

## Improvement Plan

### Phase 1: Native Git Repository Class (Non-Breaking)
**Goal**: Create foundational `GitRepository` class with native .git parsing

**Implementation**:
- Create `gh_pr_rev_md/git_utils.py` with `GitRepository` class
- Native parsing of `.git/HEAD` and `.git/config`
- Handle worktrees (`.git` file with gitdir reference)
- Support detached HEAD states
- Extract owner/repo from remote URLs

**Benefits**: 
- ~95% faster git operations (~5ms vs ~100-200ms)
- No external git binary dependency
- Better error handling for edge cases

### Phase 2: Hybrid Fallback Integration
**Goal**: Integrate native parsing with subprocess fallback

**Implementation**:
```python
def get_current_branch_pr_url(token: Optional[str] = None) -> str:
    try:
        # Try native git parsing first (new)
        repo = GitRepository()
        branch = repo.get_current_branch()
        remote_url = repo.get_remote_url()
        return construct_pr_url(remote_url, branch, token)
    except GitParsingError:
        # Fall back to subprocess (existing implementation)
        return get_current_branch_pr_url_subprocess(token)
```

### Phase 3: Enhanced Features
**Goal**: Add advanced git repository support

**Features**:
- Multiple remote support (check `branch.<branch>.remote` first)
- GitHub Enterprise host support
- Better remote URL parsing and validation
- Credential redaction for security

### Phase 4: Comprehensive Testing
**Goal**: Add missing edge case coverage

**Missing Test Cases**:
- GitHub Enterprise URLs
- Multiple remotes and branch tracking
- Worktree scenarios  
- Malformed git configs
- Permission errors
- Submodule edge cases
- Performance benchmarking

### Phase 5: Optional Dulwich Integration
**Goal**: Add Dulwich as fallback for complex edge cases

**Implementation**:
- Soft dependency on Dulwich
- Use for exotic git layouts (packed-refs, complex includes)
- Graceful degradation when not installed

## Implementation Priority

### Phase 1 Tasks (Current Focus)
- [x] Create planning document (CURRENT_REPO.md)
- [ ] Implement `GitRepository` class in `git_utils.py`
- [ ] Add comprehensive unit tests
- [ ] Integration with existing workflow (non-breaking)

### Success Metrics
- ✅ Maintains existing `.` functionality
- ✅ 95%+ performance improvement for git operations  
- ✅ Zero breaking changes to CLI interface
- ✅ Enhanced reliability for edge cases
- ✅ Path for future GitHub Enterprise support

## Architecture

### Current Flow
```
CLI "." → subprocess git calls → GitHub API/CLI → PR URL
```

### Target Flow (Hybrid)
```
CLI "." → Native GitRepository → PR URL
         ↓ (on failure)
         subprocess fallback → PR URL
```

### File Structure
```
gh_pr_rev_md/
├── git_utils.py          # New: GitRepository class
├── cli.py                # Modified: hybrid fallback
├── github_client.py      # Existing: API integration
└── formatter.py          # Existing: output formatting

tests/
├── test_git_utils.py     # New: GitRepository tests
├── test_cli.py           # Enhanced: additional scenarios
└── test_github_client.py # Existing: API tests
```

## Backward Compatibility
- All existing CLI interfaces remain unchanged
- The `.` shortcut continues to work identically
- Fallback ensures reliability even with parsing failures
- No new required dependencies (Dulwich remains optional)

---

## Comprehensive Hybrid Implementation Plan

### Consensus-Based Architecture Strategy

Based on multi-model consensus analysis, the optimal approach combines:

#### Primary Strategy: Custom Parser + Optional Dulwich Fallback
```
FALLBACK CHAIN:
Custom Parser --> Dulwich (optional) --> Manual Input
     |               |                      |
   Fast (1-3ms)   Robust (60ms)       User Control
   95% cases      Edge cases          Always works
```

#### Key Benefits Identified:
- **Performance**: Custom parsing ~1-3ms vs ~100-200ms subprocess calls
- **Reliability**: Dulwich handles exotic git layouts (worktrees, packed-refs)
- **Zero Dependencies**: Core functionality works without external tools
- **Progressive Enhancement**: Dulwich available for edge cases when installed

### Detailed Implementation Phases

#### Phase 1: Foundation and Core Git Parsing Infrastructure

**Step 1.1: Create git metadata module structure**
- [x] Create `gh_pr_rev_md/git_utils.py` with core classes:
  - `GitRepository` class for repository discovery and metadata
  - `GitParsingError` exception for handling parsing failures  
  - `RemoteInfo` dataclass for remote URL parsing results
- [x] Define interfaces and contracts between components

**Step 1.2: Implement git directory discovery**
- [x] Walk up directory tree to find `.git` (directory or file)
- [x] Handle `.git` file case (worktrees, submodules) by parsing gitdir reference
- [x] Implement path resolution for relative gitdir paths
- [x] Add error handling for non-git directories

**Step 1.3: Basic HEAD parsing for current branch**
- [x] Read `.git/HEAD` to determine current branch
- [x] Handle symbolic refs (`ref: refs/heads/branch-name`)
- [x] Handle detached HEAD state (direct commit hash)
- [x] Extract branch name from full ref path

#### Phase 2: Git Configuration and Remote URL Parsing

**Step 2.1: Implement git config parsing**
- [x] Use Python's `configparser` to read `.git/config`
- [x] Handle git-specific config format nuances (case sensitivity, section naming)
- [ ] Support basic `include.path` directives (best-effort, not recursive)
- [x] Add error handling for malformed config files

**Step 2.2: Remote URL resolution logic**
- [x] Find appropriate remote for current branch:
  - First: check `branch.<branch>.remote` config
  - Fallback: use `origin` remote if exists
  - Final fallback: use first available remote
- [x] Extract remote URL from `remote.<name>.url` config
- [x] Handle missing or invalid remote configurations

**Step 2.3: URL parsing and GitHub detection**  
- [x] Parse SSH format: `git@github.com:owner/repo.git`
- [x] Parse HTTPS format: `https://github.com/owner/repo.git`
- [x] Extract hostname, owner, repository name
- [x] Support GitHub Enterprise (custom hostnames)
- [x] Validate that remote points to GitHub-compatible host

#### Phase 3: Fallback Chain and Error Handling

**Step 3.1: Design fallback architecture**
- [ ] Create fallback chain: custom parser → Dulwich (if available) → manual input
- [x] Define clear exception hierarchy for different failure modes
- [ ] Implement soft dependency checking for Dulwich availability
- [ ] Add logging/debugging support for troubleshooting parsing issues

**Step 3.2: Dulwich integration (optional fallback)**
- [ ] Add optional Dulwich import with graceful failure
- [ ] Implement Dulwich-based branch and remote detection
- [ ] Map Dulwich results to same interface as custom parser
- [ ] Handle Dulwich-specific errors and edge cases

**Step 3.3: User experience for failures**
- [ ] Design clear error messages for each failure scenario
- [ ] Implement prompts for manual URL/branch input when automation fails
- [ ] Add `--branch` and `--remote` CLI flags for manual override
- [ ] Provide helpful debugging information (which parsing step failed)

#### Phase 4: CLI Integration and Interface Design

**Step 4.1: Modify CLI argument parsing**
- [ ] Update Click command in `cli.py` to make `pr_url` argument optional
- [ ] Add new flags: `--branch`, `--remote`, `--manual-url` for overrides
- [ ] Add `--git-debug` flag for troubleshooting git parsing issues
- [ ] Maintain backward compatibility (existing scripts with URLs still work)

**Step 4.2: Integrate git parsing into main workflow**
- [ ] Modify main CLI function to attempt git auto-detection first
- [ ] Construct PR URL from detected git info: `https://{host}/{owner}/{repo}/pull/{pr_number}`
- [ ] Handle PR number detection (may require GitHub API call to find open PR for branch)
- [ ] Add fallback to original manual URL behavior when auto-detection fails

**Step 4.3: Security implementation - credential redaction**
- [ ] Implement credential scrubbing for remote URLs containing auth tokens
- [ ] Ensure no credentials are logged or displayed in error messages
- [ ] Add security tests for various credential formats in URLs
- [ ] Document security considerations for users

#### Phase 5: Comprehensive Testing Strategy

**Step 5.1: Unit testing for git parsing components**
- [ ] Create test fixtures for various git repository states:
  - Normal repos with branches and remotes
  - Detached HEAD states  
  - Worktree scenarios (`.git` file with gitdir reference)
  - Missing/malformed configs
  - Multiple remotes with different priorities
- [ ] Test edge cases: empty repos, shallow clones, submodules
- [ ] Mock file system for controlled testing environments

**Step 5.2: Integration testing**
- [ ] Test complete workflow: git detection → PR URL construction → GitHub API calls
- [ ] Test fallback chain: custom parser failure → Dulwich → manual input
- [ ] Test CLI interface with various argument combinations
- [ ] Test cross-platform compatibility (Windows, macOS, Linux path handling)
- [ ] Performance testing: measure startup time impact

**Step 5.3: Security and error handling tests** 
- [ ] Test credential redaction in various URL formats
- [ ] Test error handling for permission denied, corrupted files
- [ ] Test security: ensure no sensitive data in logs/output
- [ ] Test user experience: clear error messages, helpful debugging info
- [ ] Regression testing: ensure existing functionality still works

#### Phase 6: Performance Optimization and Documentation

**Step 6.1: Performance analysis and optimization**
- [ ] Benchmark startup time: baseline vs with git parsing
- [ ] Profile git parsing operations to identify bottlenecks
- [ ] Optimize file I/O: minimize disk reads, cache results if beneficial
- [ ] Lazy loading: only parse git info when needed, avoid upfront costs
- [ ] Compare performance: custom parser vs Dulwich for common cases

**Step 6.2: Documentation and developer experience**
- [ ] Update README with new auto-detection capabilities
- [ ] Document new CLI flags and their usage patterns
- [ ] Add troubleshooting guide for git parsing issues  
- [ ] Document security considerations for enterprise users
- [ ] Add code documentation/docstrings for git parsing API

**Step 6.3: Packaging and dependency management**
- [ ] Add optional Dulwich dependency to setup.py/pyproject.toml
- [ ] Test installation scenarios: with/without Dulwich
- [ ] Update CI/CD to test both dependency configurations
- [ ] Document installation options for different user needs
- [ ] Consider package size impact and distribution optimization

#### Phase 7: Release Preparation and Final Integration

**Step 7.1: Final validation and quality assurance**
- [ ] Run complete test suite across multiple environments
- [ ] Validate security: run security scanning tools, manual security review
- [ ] Performance validation: ensure startup time meets target
- [ ] User acceptance testing: test with various real-world git repositories
- [ ] Backward compatibility verification: ensure existing workflows unaffected

**Step 7.2: Release engineering**
- [ ] Version bump and changelog preparation
- [ ] Tag release with clear migration notes for users
- [ ] Update package metadata and dependencies
- [ ] Prepare release notes highlighting new auto-detection capabilities
- [ ] Test final package builds and distribution

**Step 7.3: Rollout strategy and monitoring**
- [ ] Plan gradual rollout: beta users first, then general availability
- [ ] Set up monitoring for new failure modes (git parsing errors)
- [ ] Prepare support documentation for common issues  
- [ ] Create feedback collection mechanism for edge cases
- [ ] Plan follow-up iterations based on user feedback

### Critical Success Criteria

- 95%+ of users can run tool without manual URL input
- Startup time impact minimal (< 50ms overhead)
- Graceful fallback when automation fails
- Zero security vulnerabilities (no credential exposure)
- Backward compatibility maintained
- Comprehensive test coverage across git repository types

---

**Current Progress**: Phase 1 GitRepository class implementation completed. Next: comprehensive unit testing.