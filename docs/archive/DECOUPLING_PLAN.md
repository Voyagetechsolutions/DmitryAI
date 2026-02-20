# Decoupling Plan: Remove PDRI Integration from Dmitry

## Problem
Built a three-way dependency chain (Dmitry ↔ PDRI ↔ Aegis) instead of clean architecture where only the Platform knows all services.

## Goal
Make Dmitry and Aegis standalone services that connect to Platform individually. No direct coupling to PDRI.

## Architecture Principles
✅ PDRI should not know Aegis exists
✅ Aegis should not know PDRI exists (beyond "I emit events")
✅ Dmitry should not know PDRI/Aegis exist (beyond "I call tools")
✅ Only the Platform knows all three

## Files to Remove/Modify

### 1. Files to DELETE (Direct PDRI Coupling)
- `MarkX/integrations/pdri_client.py` - Direct PDRI API client
- `MarkX/integrations/pdri_listener.py` - PDRI WebSocket listener
- `MarkX/dmitry_operator/pdri_intent.py` - PDRI-specific intent detection
- `MarkX/tools/security/pdri_tools.py` - PDRI-specific tools

### 2. Files to MODIFY (Remove PDRI References)
- `MarkX/integrations/__init__.py` - Remove PDRI exports
- `MarkX/dmitry_operator/orchestrator.py` - Remove PDRI intent detection
- `MarkX/modes/security_mode_enhanced.py` - Remove PDRI connection check

### 3. New Architecture

#### Dmitry Tools (Platform-based)
Replace PDRI tools with Platform tools:
- `platform.get_risk_findings(filters)` → replaces pdri_risk_lookup
- `platform.get_finding_details(id)` → replaces pdri_risk_explain
- `platform.search_entities(query)` → replaces pdri_high_risk_scan
- `platform.propose_actions(finding_id)` → new
- `platform.execute_action(action_id, action_type)` → new

#### Dmitry Contract
Dmitry only knows:
- Platform API endpoint (from env: PLATFORM_API_URL)
- Platform API key (from env: PLATFORM_API_KEY)
- Tool calling interface

Dmitry does NOT know:
- PDRI exists
- Aegis exists
- Neo4j exists
- Internal Platform architecture

## Migration Steps

### Phase 1: Document Current State ✓
- Identified all PDRI coupling points
- Documented files to remove/modify

### Phase 2: Remove PDRI Integration (This Phase)
1. Delete PDRI-specific files
2. Remove PDRI imports from remaining files
3. Update integrations package
4. Clean up orchestrator
5. Clean up security mode

### Phase 3: Create Platform Tools (Next)
1. Create `MarkX/tools/platform/` directory
2. Implement Platform client
3. Implement Platform tools
4. Register Platform tools

### Phase 4: Update Documentation
1. Remove PDRI references from docs
2. Add Platform integration docs
3. Update deployment guides

## Success Criteria
✅ Dmitry runs with PDRI completely offline
✅ Dmitry only calls Platform API
✅ No code references to PDRI schemas remain
✅ Zero direct network dependencies on PDRI
✅ All tests pass without PDRI running

## Rollback Plan
If issues arise:
1. Git revert to before decoupling
2. Re-evaluate architecture
3. Implement proper Platform layer first
