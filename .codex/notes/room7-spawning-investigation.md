# Complete Battle Issues Investigation - Room 4-7 Analysis

## Issue Description
User reported that battles around room 4-5 would appear to "endlessly spawn new foes or restart themselves", making the game feel stuck or broken. Investigation through actual gameplay from Room 2 to Room 5 confirms **two distinct but related issues**.

## Two-Part Root Cause Confirmed

### 1. Frontend Polling Issue (RESOLVED ✅)
**Problem**: Frontend was polling at hardcoded 60 FPS regardless of user settings
**Solution**: Implemented proper framerate-based polling respecting user settings (30/60/120 FPS)
**Code Fix**: `setTimeout(pollBattle, 1000 / framerate)` where framerate loads from localStorage
**Impact**: Reduces backend load by up to 50% for users choosing 30 FPS

### 2. Backend Mid-Battle Enemy Spawning (DISCOVERED ⚠️)
**Problem**: Certain enemies have summoning abilities that spawn additional foes mid-battle
**Evidence**: Room 5 "Noxious Becca" with "Menagerie Bond" spawned "becca jellyfish electric summon" during combat
**User Impact**: Battles feel "endless" because enemy count increases unexpectedly mid-fight

## Battle Progression Analysis

### Room 2: Baseline
- **Duration**: 4 seconds
- **Events**: 8 
- **Enemy**: Single Kboshi
- **Complexity**: Simple, fast battle

### Room 3: Moderate
- **Duration**: 5 seconds  
- **Events**: 21
- **Enemy**: Single Luna with DoT effects
- **Complexity**: DoT mechanics introduced

### Room 4: High Complexity
- **Duration**: 17 seconds
- **Events**: 243 (30x increase!)
- **Enemy**: Single Ixia with complex interactions  
- **Backend Load**: 2000+ requests logged
- **Response Size**: 10,558+ bytes

### Room 5: Extreme + Spawning
- **Duration**: 60+ seconds (ongoing during investigation)
- **Events**: 3000+ (logs dropped 3241 lines)
- **Enemies**: Noxious Becca + **spawned jellyfish** (mid-battle)
- **Backend Load**: Thousands of requests with 12,609+ byte responses
- **Spawning Confirmed**: Screenshot evidence of two simultaneous enemies

## Combined Effect Analysis
1. **Early rooms (2-3)**: Fast battles, minimal polling impact
2. **Mid rooms (4-5)**: Complex battles with exponential event growth
3. **Polling amplification**: 60 FPS × complex battles = request flooding
4. **Spawning confusion**: New enemies appearing makes battles feel broken
5. **Performance degradation**: Slow responses + unexpected spawning = "endless battle" perception

## Technical Evidence

### Backend Logs
```
Room 4: "dropped 2126 lines from the middle"
Room 5: "dropped 3241 lines from the middle"
Constant ticking: "becca Abyssal Corruption tick", "becca Noxious tick"
Massive damage exchanges: "becca takes 1 from player" repeatedly
```

### Frontend Polling Fix
```javascript
// Before: Hardcoded 60 FPS
setTimeout(pollBattle, 1000 / 60);

// After: User framerate setting
setTimeout(pollBattle, 1000 / framerate); // 30/60/120 FPS options
```

### Spawning Evidence
- Screenshot shows original Noxious Becca + spawned jellyfish fighting simultaneously
- UI clearly displays two separate enemy health bars
- Mid-battle enemy appearance matches "endless spawning" user reports

## Recommendations

### Frontend (COMPLETED ✅)
- ✅ Implement framerate-based polling to respect user preferences
- ✅ Load settings from localStorage with proper fallbacks
- ✅ Allow users to optimize performance via System Settings

### Backend (NEEDS INVESTIGATION ⚠️) 
- 🔍 Review enemy spawning mechanics for clarity/balance
- 🔍 Consider spawn notifications to set player expectations
- 🔍 Evaluate if mid-battle spawning should be limited in early floors
- 🔍 Optimize response payload sizes for complex battles

## User Experience Impact
- **Frontend fix**: Reduces backend load and respects user preferences
- **Spawning issue**: Still causes unexpected difficulty and confusion
- **Combined perception**: Battles feel more responsive but spawning still surprising

## Investigation Status
- ✅ **Polling frequency**: Fixed and working correctly
- ⚠️ **Mid-battle spawning**: Confirmed as separate backend issue requiring design review
- 📋 **Documentation**: Complete investigation saved for future reference

## Timestamp
2025-09-13 23:37:00 - Investigation completed through Room 5 with spawning evidence