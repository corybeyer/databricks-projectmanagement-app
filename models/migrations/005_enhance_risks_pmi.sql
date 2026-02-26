-- ============================================================
-- Migration 005: Enhance risks table with PMI risk management fields
-- ============================================================
-- Phase 0.3 — PMI Risk Management Schema Enhancement
-- Adds 12 new columns for full PMI PMBOK risk lifecycle support
-- Also updates status lifecycle from simple to PMI-aligned
-- ============================================================

USE workspace.project_management;

-- Response strategy (PMI: avoid, transfer, mitigate, accept, escalate)
ALTER TABLE risks ADD COLUMN response_strategy STRING COMMENT 'avoid | transfer | mitigate | accept | escalate';

-- Contingency plan — fallback if risk materializes
ALTER TABLE risks ADD COLUMN contingency_plan STRING COMMENT 'Fallback plan if risk materializes';

-- Trigger conditions — early warning signs
ALTER TABLE risks ADD COLUMN trigger_conditions STRING COMMENT 'Early warning signs / risk triggers';

-- Risk proximity — when the risk may occur
ALTER TABLE risks ADD COLUMN risk_proximity STRING COMMENT 'near_term | mid_term | long_term';

-- Risk urgency — how soon response is needed (1-5)
ALTER TABLE risks ADD COLUMN risk_urgency INT COMMENT '1-5 scale — how soon response needed';

-- Residual probability — probability after response applied (1-5)
ALTER TABLE risks ADD COLUMN residual_probability INT COMMENT '1-5 — probability after response';

-- Residual impact — impact after response applied (1-5)
ALTER TABLE risks ADD COLUMN residual_impact INT COMMENT '1-5 — impact after response';

-- Residual score — residual_probability x residual_impact
ALTER TABLE risks ADD COLUMN residual_score INT COMMENT 'residual_probability × residual_impact';

-- Secondary risks — new risks introduced by the response
ALTER TABLE risks ADD COLUMN secondary_risks STRING COMMENT 'New risks introduced by the response';

-- Identified date — when risk was first identified
ALTER TABLE risks ADD COLUMN identified_date DATE COMMENT 'When risk was first identified';

-- Last review date — when risk was last reviewed
ALTER TABLE risks ADD COLUMN last_review_date DATE COMMENT 'When risk was last reviewed';

-- Response owner — who executes the response (may differ from risk owner)
ALTER TABLE risks ADD COLUMN response_owner STRING COMMENT 'Who executes the response (may differ from risk owner)';

-- Update status comment to reflect new PMI lifecycle
-- Note: COMMENT ON COLUMN syntax for Databricks/Delta
-- Status values: identified | qualitative_analysis | response_planning | monitoring | resolved | closed
ALTER TABLE risks ALTER COLUMN status COMMENT 'identified | qualitative_analysis | response_planning | monitoring | resolved | closed';
