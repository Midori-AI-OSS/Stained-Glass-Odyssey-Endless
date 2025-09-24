# Detailed Test Failure Catalog

**Audit ID:** 85d9596b-test-failures-catalog  
**Date:** September 24, 2024  
**Scope:** Detailed analysis of all failing tests with specific error patterns

## Backend Test Failures (128 tests)

### Category 1: LLM Dependency Failures (Primary Pattern)

**Error Pattern:** `ModuleNotFoundError: No module named 'llms.torch_checker'; 'llms' is not a package`

**Affected Tests (Sample):**
1. `test_app.py` - 4 tests (test_status_endpoint, test_run_flow, test_players_and_rooms, test_room_images)
2. `test_app_without_llm_deps.py` - All tests
3. `test_battle_defeat.py` - test_run_battle_handles_defeat_cleanup
4. `test_battle_end_on_all_foes_dead.py` - Integration tests
5. `test_battle_engine_async.py` - Battle orchestration tests
6. `test_character_editor.py` - Character management tests
7. `test_player_editor.py` - Player customization tests
8. `test_party_endpoint.py` - Party management API tests
9. `test_run_persistence.py` - Save/load functionality tests
10. `test_save_management.py` - Data persistence tests

**Root Cause:** The application code imports `from llms.torch_checker import is_torch_available` but this module is not properly available in the test environment. The conftest.py attempts to stub LLM modules but is missing the torch_checker specifically.

**Fix Location:** `/backend/conftest.py` needs to include torch_checker stub in `_ensure_llm_stub()` function.

### Category 2: Import/Module Structure Failures

**Error Patterns:** Various import-related errors

**Affected Tests:**
1. `test_accelerate_dependency.py` - Accelerate package import issues
2. `test_accelerate_fix_verification.py` - Same as above
3. `test_torch_checker.py` - Direct torch checker functionality tests

**Root Cause:** Module structure changes or missing dependencies in test environment.

### Category 3: Integration Test Failures

**Error Pattern:** Tests that depend on complex game state or backend services

**Affected Tests (Sample):**
1. `test_aggro_property.py` - Aggro system integration
2. `test_battle_logging.py` - Battle event logging
3. `test_battle_rewards.py` - Reward calculation and distribution
4. `test_card_effects.py` - Card effect application
5. `test_enhanced_enrage.py` - Enhanced enrage mechanics
6. `test_exp_leveling.py` - Experience and leveling system
7. `test_gacha.py` - Gacha/pull system
8. `test_new_upgrade_system.py` - Character upgrade mechanics

**Root Cause:** These tests require complex game state initialization that fails due to the LLM dependency issue.

## Frontend Test Failures (5 tests)

### Category 1: Missing Asset Files

**Test:** `assets.test.js`  
**Error:** `ENOENT: no such file or directory, open '/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/frontend/src/lib/assets/cards/gray/bg_attack_default_gray.png'`

**Details:**
- Test expects specific card background image files
- Files may have been moved, renamed, or never committed
- Function `pngSize()` attempts to read non-existent PNG files

**Missing Files:**
- `bg_attack_default_gray.png` in cards/gray directory
- Potentially other card background assets

### Category 2: Component API Mismatches

**Test:** `actionqueue.test.js`  
**Failing Cases:**
- "ActionQueue component > renders portraits and optional action values"
- "ActionQueue component > includes a turn counter tile with enrage-aware markup"

**Error:** `turn counter entry markup missing`

**Details:**
- Test expects specific DOM elements with certain CSS classes
- Component structure may have changed
- Looking for elements with `class="entry turn-counter"`

### Category 3: State Management Issues

**Test:** `stat-tabs-persistence.test.js`  
**Failing Cases:**
- "StatTabs editor persistence > stores editor values by character id"
- "StatTabs editor persistence > restores cached values when switching"

**Details:**
- Tests expect localStorage or state persistence functionality
- Character ID-based storage may not be working as expected
- Cache/restore mechanism may have changed

### Category 4: Backend Integration Issues

**Test:** `battlepolling.test.js`  
**Error:** `ReferenceError: shouldHandleRunEndError is not defined`

**Details:**
- Test tries to use undefined function `shouldHandleRunEndError`
- Function may have been removed or renamed
- Battle polling logic integration with backend error handling

### Category 5: Data Persistence Issues

**Test:** `start-run-damage-type.test.js`  
**Error:** `expect(received).toBe(expected) Expected: "Fire" Received: "Light"`

**Details:**
- Test expects damage type persistence to work correctly
- Default or saved damage type is "Light" when test expects "Fire"
- Damage type configuration or persistence logic may have changed

## Pattern Analysis

### Common Failure Causes

1. **Environment Configuration Issues (80% of backend failures)**
   - LLM dependency stubbing incomplete
   - Test environment doesn't match development environment

2. **Asset Management Issues (Frontend)**
   - Missing or moved asset files
   - Asset path changes not reflected in tests

3. **API Evolution (Both Backend and Frontend)**
   - Component interfaces changed but tests not updated
   - Function signatures or return values modified

4. **State Management Changes**
   - Persistence mechanisms modified
   - Default values or initialization logic changed

### Test Age Assessment

**Recently Maintained Tests (Likely Passing):**
- Core game mechanics tests
- Basic utility function tests
- Simple component rendering tests

**Outdated Tests (Likely Need Updates):**
- Integration tests with complex dependencies
- Tests that depend on specific file structures
- Tests with hardcoded expectations about system behavior

**Infrastructure Tests (Need Environment Fixes):**
- All app initialization tests
- Database and persistence tests
- Service layer tests

## Specific Error Examples

### Backend Example 1: test_app.py
```
ERROR at setup of test_status_endpoint 
ModuleNotFoundError: No module named 'llms.torch_checker'; 'llms' is not a package
```
**Location:** app.py:9  
**Code:** `from llms.torch_checker import is_torch_available`

### Frontend Example 1: assets.test.js
```javascript
function pngSize(path) {
  const buf = readFileSync(path); // Fails here
  // ...
}
```
**Missing File:** `/src/lib/assets/cards/gray/bg_attack_default_gray.png`

### Frontend Example 2: actionqueue.test.js
```javascript
const [turnCounter] = findElements(ast.html, (node) => 
  hasStaticClass(node, 'entry') && hasStaticClass(node, 'turn-counter')
);
expect(turnCounter, 'turn counter entry markup missing').toBeDefined();
```
**Issue:** Component no longer generates expected DOM structure

## Recommended Fix Priorities

### Priority 1 (Immediate - Fixes 80% of backend failures)
1. Fix LLM dependency stubbing in conftest.py
2. Add torch_checker module stub

### Priority 2 (Quick wins - Fixes 5 frontend failures)  
1. Create missing asset placeholder files
2. Update component API expectations
3. Fix undefined function references

### Priority 3 (Systematic cleanup)
1. Review and update all import statements
2. Modernize test expectations to match current code
3. Improve test environment isolation

---

**Total Issues Identified:** 133 failing tests  
**Primary Root Cause:** Test environment configuration (LLM dependencies)  
**Secondary Issues:** Missing assets, outdated test expectations, API evolution

*End of Failure Catalog*