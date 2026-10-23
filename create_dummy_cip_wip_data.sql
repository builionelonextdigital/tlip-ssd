-- Create dummy data for CIP/WIP Summary Report
-- This script creates:
--   1. Budget categories and budget codes (for cost classification)
--   2. CIP/WIP accounts (2411, 2412)
--   3. Analytic accounts (budget code tracking)
--   4. Development projects (actual project entities)
--   5. Journal entries (account_move) with project linkage
--   6. Journal items (account_move_line) with analytic distribution
--
-- The data structure follows:
--   Development Project -> Journal Entry -> Journal Items -> Budget Codes (via analytic_distribution)

-- Step 1: Create Budget Categories (no active column)
INSERT INTO budget_category (id, name, code, create_uid, write_uid, create_date, write_date)
VALUES
    (1, 'Construction', 'CONST', 3, 3, NOW(), NOW()),
    (2, 'Infrastructure', 'INFRA', 3, 3, NOW(), NOW()),
    (3, 'Equipment', 'EQUIP', 3, 3, NOW(), NOW()),
    (4, 'Development', 'DEV', 3, 3, NOW(), NOW()),
    (5, 'Facilities', 'FAC', 3, 3, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Update sequence for budget_category
SELECT setval('budget_category_id_seq', (SELECT MAX(id) FROM budget_category));

-- Step 2: Create Budget Codes
INSERT INTO budget_code (id, code, name, budget_category_id, active, create_uid, write_uid, create_date, write_date)
VALUES
    (1, 'INV-01-01', 'Building Construction', 1, true, 3, 3, NOW(), NOW()),
    (2, 'INV-01-02', 'Structural Work', 1, true, 3, 3, NOW(), NOW()),
    (3, 'INV-02-01', 'Road Infrastructure', 2, true, 3, 3, NOW(), NOW()),
    (4, 'INV-02-02', 'Utilities Infrastructure', 2, true, 3, 3, NOW(), NOW()),
    (5, 'INV-03-01', 'Machinery', 3, true, 3, 3, NOW(), NOW()),
    (6, 'INV-03-02', 'Office Equipment', 3, true, 3, 3, NOW(), NOW()),
    (7, 'INV-04-01', 'Land Development', 4, true, 3, 3, NOW(), NOW()),
    (8, 'INV-04-02', 'Site Preparation', 4, true, 3, 3, NOW(), NOW()),
    (9, 'INV-05-01', 'Factory Facilities', 5, true, 3, 3, NOW(), NOW()),
    (10, 'INV-05-02', 'Warehouse Facilities', 5, true, 3, 3, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Update sequence for budget_code
SELECT setval('budget_code_id_seq', (SELECT MAX(id) FROM budget_code));

-- Step 3: Create CIP/WIP Accounts (2411 and 2412)
INSERT INTO account_account (
    id, code_store, name, account_type, deprecated, reconcile,
    non_trade, create_asset, multiple_assets_per_line,
    create_uid, write_uid, create_date, write_date
)
VALUES
    (
        1001,
        '{"1": "2411"}',
        '{"en_US": "Construction in Progress - Buildings"}',
        'asset_non_current',
        false,
        false,
        false,
        'no',
        false,
        3, 3, NOW(), NOW()
    ),
    (
        1002,
        '{"1": "2412"}',
        '{"en_US": "Construction in Progress - Infrastructure"}',
        'asset_non_current',
        false,
        false,
        false,
        'no',
        false,
        3, 3, NOW(), NOW()
    )
ON CONFLICT (id) DO NOTHING;

-- Update sequence for account_account
SELECT setval('account_account_id_seq', (SELECT MAX(id) FROM account_account));

-- Step 4: Create Analytic Accounts (Budget Code Accounts)
-- These are NOT the actual projects, but budget code tracking accounts
-- Each analytic account is linked to a budget_code for cost classification
INSERT INTO account_analytic_account (
    id, plan_id, root_plan_id, company_id, code, name, active,
    budget_code_id, budget_category_id, state,
    create_uid, write_uid, create_date, write_date
)
VALUES
    -- Construction Projects (Account 2411)
    (1, 1, 1, 1, 'CIP071', '{"en_US": "Office Building Phase 1"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (2, 1, 1, 1, 'CIP072', '{"en_US": "Office Building Phase 2"}', true, 2, 1, 'open', 3, 3, NOW(), NOW()),
    (3, 1, 1, 1, 'CIP073', '{"en_US": "Warehouse Construction"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (4, 1, 1, 1, 'CIP074', '{"en_US": "Parking Structure"}', true, 2, 1, 'open', 3, 3, NOW(), NOW()),
    (5, 1, 1, 1, 'CIP075', '{"en_US": "Main Production Building"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (6, 1, 1, 1, 'CIP076', '{"en_US": "Administration Building"}', true, 2, 1, 'open', 3, 3, NOW(), NOW()),
    (7, 1, 1, 1, 'CIP077', '{"en_US": "Storage Facility Block A"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (8, 1, 1, 1, 'CIP078', '{"en_US": "Storage Facility Block B"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (9, 1, 1, 1, 'CIP079', '{"en_US": "Quality Control Laboratory"}', true, 2, 1, 'open', 3, 3, NOW(), NOW()),
    (10, 1, 1, 1, 'CIP080', '{"en_US": "Employee Cafeteria"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),

    -- Infrastructure Projects (Account 2412)
    (11, 1, 1, 1, 'CIP081', '{"en_US": "Road Network Development"}', true, 3, 2, 'open', 3, 3, NOW(), NOW()),
    (12, 1, 1, 1, 'CIP082', '{"en_US": "Water Supply System"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (13, 1, 1, 1, 'CIP083', '{"en_US": "Electrical Grid Expansion"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (14, 1, 1, 1, 'CIP084', '{"en_US": "Drainage System Phase 1"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (15, 1, 1, 1, 'CIP085', '{"en_US": "Telecommunications Network"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (16, 1, 1, 1, 'CIP086', '{"en_US": "Fire Protection System"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (17, 1, 1, 1, 'CIP087', '{"en_US": "Sewage Treatment Plant"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (18, 1, 1, 1, 'CIP088', '{"en_US": "Security System Integration"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (19, 1, 1, 1, 'CIP089', '{"en_US": "HVAC Central System"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (20, 1, 1, 1, 'CIP090', '{"en_US": "Gas Pipeline Installation"}', true, 3, 2, 'open', 3, 3, NOW(), NOW()),

    -- Equipment Projects
    (21, 1, 1, 1, 'CIP091', '{"en_US": "Manufacturing Equipment Line 1"}', true, 5, 3, 'open', 3, 3, NOW(), NOW()),
    (22, 1, 1, 1, 'CIP092', '{"en_US": "Manufacturing Equipment Line 2"}', true, 5, 3, 'open', 3, 3, NOW(), NOW()),
    (23, 1, 1, 1, 'CIP093', '{"en_US": "Packaging Machinery"}', true, 5, 3, 'open', 3, 3, NOW(), NOW()),
    (24, 1, 1, 1, 'CIP094', '{"en_US": "Material Handling Equipment"}', true, 5, 3, 'open', 3, 3, NOW(), NOW()),
    (25, 1, 1, 1, 'CIP095', '{"en_US": "Office IT Infrastructure"}', true, 6, 3, 'open', 3, 3, NOW(), NOW()),
    (26, 1, 1, 1, 'CIP096', '{"en_US": "Warehouse Automation System"}', true, 5, 3, 'open', 3, 3, NOW(), NOW()),

    -- Development Projects
    (27, 1, 1, 1, 'CIP101', '{"en_US": "Site Clearing and Grading"}', true, 8, 4, 'open', 3, 3, NOW(), NOW()),
    (28, 1, 1, 1, 'CIP102', '{"en_US": "Land Development Zone A"}', true, 7, 4, 'open', 3, 3, NOW(), NOW()),
    (29, 1, 1, 1, 'CIP103', '{"en_US": "Land Development Zone B"}', true, 7, 4, 'open', 3, 3, NOW(), NOW()),
    (30, 1, 1, 1, 'CIP104', '{"en_US": "Industrial Park Phase 1"}', true, 8, 4, 'open', 3, 3, NOW(), NOW()),
    (31, 1, 1, 1, 'CIP105', '{"en_US": "Industrial Park Phase 2"}', true, 8, 4, 'open', 3, 3, NOW(), NOW()),

    -- Facilities Projects
    (32, 1, 1, 1, 'CIP111', '{"en_US": "Factory Complex A"}', true, 9, 5, 'open', 3, 3, NOW(), NOW()),
    (33, 1, 1, 1, 'CIP112', '{"en_US": "Factory Complex B"}', true, 9, 5, 'open', 3, 3, NOW(), NOW()),
    (34, 1, 1, 1, 'CIP113', '{"en_US": "Cold Storage Warehouse"}', true, 10, 5, 'open', 3, 3, NOW(), NOW()),
    (35, 1, 1, 1, 'CIP114', '{"en_US": "Distribution Center"}', true, 10, 5, 'open', 3, 3, NOW(), NOW()),
    (36, 1, 1, 1, 'CIP115', '{"en_US": "Maintenance Workshop"}', true, 9, 5, 'open', 3, 3, NOW(), NOW()),

    -- Additional Mixed Projects
    (37, 1, 1, 1, 'CIP121', '{"en_US": "Solar Power Installation"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (38, 1, 1, 1, 'CIP122', '{"en_US": "Environmental Protection System"}', true, 4, 2, 'open', 3, 3, NOW(), NOW()),
    (39, 1, 1, 1, 'CIP123', '{"en_US": "Employee Dormitory"}', true, 1, 1, 'open', 3, 3, NOW(), NOW()),
    (40, 1, 1, 1, 'CIP124', '{"en_US": "Recreation Facilities"}', true, 2, 1, 'open', 3, 3, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Update sequence for account_analytic_account
SELECT setval('account_analytic_account_id_seq', (SELECT MAX(id) FROM account_analytic_account));

-- Step 5: Create Development Projects
-- These represent the actual projects that CIP/WIP costs are tracked against
INSERT INTO development_project (id, code, name, company_id, create_uid, write_uid, create_date, write_date)
VALUES
    -- Construction Projects
    (1, 'PRJ-001', 'Office Complex Development', 1, 3, 3, NOW(), NOW()),
    (2, 'PRJ-002', 'Warehouse Development Project', 1, 3, 3, NOW(), NOW()),
    (3, 'PRJ-003', 'Production Facility Construction', 1, 3, 3, NOW(), NOW()),
    (4, 'PRJ-004', 'Quality Control Center', 1, 3, 3, NOW(), NOW()),

    -- Infrastructure Projects
    (5, 'PRJ-005', 'Site Infrastructure Development', 1, 3, 3, NOW(), NOW()),
    (6, 'PRJ-006', 'Utilities Installation Project', 1, 3, 3, NOW(), NOW()),
    (7, 'PRJ-007', 'Environmental Systems Project', 1, 3, 3, NOW(), NOW()),

    -- Equipment Projects
    (8, 'PRJ-008', 'Manufacturing Equipment Installation', 1, 3, 3, NOW(), NOW()),
    (9, 'PRJ-009', 'IT Infrastructure Project', 1, 3, 3, NOW(), NOW()),

    -- Development Projects
    (10, 'PRJ-010', 'Land Development Initiative', 1, 3, 3, NOW(), NOW()),
    (11, 'PRJ-011', 'Industrial Park Development', 1, 3, 3, NOW(), NOW()),

    -- Facilities Projects
    (12, 'PRJ-012', 'Factory Complex Project', 1, 3, 3, NOW(), NOW()),
    (13, 'PRJ-013', 'Cold Storage Development', 1, 3, 3, NOW(), NOW()),
    (14, 'PRJ-014', 'Support Facilities Project', 1, 3, 3, NOW(), NOW()),

    -- Additional Projects
    (15, 'PRJ-015', 'Renewable Energy Project', 1, 3, 3, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Update sequence for development_project
SELECT setval('development_project_id_seq', (SELECT MAX(id) FROM development_project));

-- Step 6: Create Journal Entries (Account Moves) with Development Project linkage
-- Creating moves for a full year (2024) with varied transactions
INSERT INTO account_move (
    id, name, date, ref, state, move_type, journal_id,
    company_id, currency_id, auto_post, development_project_id,
    create_uid, write_uid, create_date, write_date
)
VALUES
    (1001, 'MISC/2024/001', '2024-01-15', 'Opening Balance CIP', 'posted', 'entry', 8, 1, 23, 'no', 1, 3, 3, NOW(), NOW()),
    (1002, 'MISC/2024/002', '2024-01-25', 'January CIP Additions', 'posted', 'entry', 8, 1, 23, 'no', 2, 3, 3, NOW(), NOW()),
    (1003, 'MISC/2024/003', '2024-02-10', 'February CIP Additions', 'posted', 'entry', 8, 1, 23, 'no', 1, 3, 3, NOW(), NOW()),
    (1004, 'MISC/2024/004', '2024-02-28', 'February Equipment', 'posted', 'entry', 8, 1, 23, 'no', 8, 3, 3, NOW(), NOW()),
    (1005, 'MISC/2024/005', '2024-03-15', 'March Construction', 'posted', 'entry', 8, 1, 23, 'no', 2, 3, 3, NOW(), NOW()),
    (1006, 'MISC/2024/006', '2024-03-28', 'March Infrastructure', 'posted', 'entry', 8, 1, 23, 'no', 5, 3, 3, NOW(), NOW()),
    (1007, 'MISC/2024/007', '2024-04-10', 'April Materials', 'posted', 'entry', 8, 1, 23, 'no', 1, 3, 3, NOW(), NOW()),
    (1008, 'MISC/2024/008', '2024-04-25', 'April Labor', 'posted', 'entry', 8, 1, 23, 'no', 3, 3, 3, NOW(), NOW()),
    (1009, 'MISC/2024/009', '2024-05-12', 'May Mixed Projects', 'posted', 'entry', 8, 1, 23, 'no', 1, 3, 3, NOW(), NOW()),
    (1010, 'MISC/2024/010', '2024-05-28', 'May Development', 'posted', 'entry', 8, 1, 23, 'no', 10, 3, 3, NOW(), NOW()),
    (1011, 'MISC/2024/011', '2024-06-10', 'June Equipment Install', 'posted', 'entry', 8, 1, 23, 'no', 8, 3, 3, NOW(), NOW()),
    (1012, 'MISC/2024/012', '2024-06-25', 'June Transfer to FA', 'posted', 'entry', 8, 1, 23, 'no', 2, 3, 3, NOW(), NOW()),
    (1013, 'MISC/2024/013', '2024-07-08', 'July Construction', 'posted', 'entry', 8, 1, 23, 'no', 11, 3, 3, NOW(), NOW()),
    (1014, 'MISC/2024/014', '2024-07-22', 'July Utilities', 'posted', 'entry', 8, 1, 23, 'no', 6, 3, 3, NOW(), NOW()),
    (1015, 'MISC/2024/015', '2024-08-05', 'August Facilities', 'posted', 'entry', 8, 1, 23, 'no', 12, 3, 3, NOW(), NOW()),
    (1016, 'MISC/2024/016', '2024-08-20', 'August Site Work', 'posted', 'entry', 8, 1, 23, 'no', 14, 3, 3, NOW(), NOW()),
    (1017, 'MISC/2024/017', '2024-09-10', 'September Projects', 'posted', 'entry', 8, 1, 23, 'no', 7, 3, 3, NOW(), NOW()),
    (1018, 'MISC/2024/018', '2024-09-25', 'September Infrastructure', 'posted', 'entry', 8, 1, 23, 'no', 5, 3, 3, NOW(), NOW()),
    (1019, 'MISC/2024/019', '2024-10-08', 'October Multi-Project', 'posted', 'entry', 8, 1, 23, 'no', 1, 3, 3, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Update sequence for account_move
SELECT setval('account_move_id_seq', (SELECT MAX(id) FROM account_move));

-- Step 7: Create Account Move Lines (Journal Items) with Analytic Distribution
-- Comprehensive data covering all 40 projects throughout 2024
-- Note: development_project_id will be computed from move_id.development_project_id
INSERT INTO account_move_line (
    id, move_id, account_id, date, invoice_date, name, debit, credit,
    balance, amount_currency, parent_state, display_type,
    journal_id, company_id, company_currency_id, currency_id,
    analytic_distribution,
    create_uid, write_uid, create_date, write_date
)
VALUES
    -- Move 1001: Opening Balances for major projects (Jan 15)
    (10001, 1001, 1001, '2024-01-15', '2024-01-15', 'Opening CIP071', 500000000, 0, 500000000, 500000000, 'posted', 'product', 8, 1, 23, 23, '{"1": 100}', 3, 3, NOW(), NOW()),
    (10002, 1001, 1001, '2024-01-15', '2024-01-15', 'Opening CIP072', 350000000, 0, 350000000, 350000000, 'posted', 'product', 8, 1, 23, 23, '{"2": 100}', 3, 3, NOW(), NOW()),
    (10003, 1001, 1001, '2024-01-15', '2024-01-15', 'Opening CIP075', 425000000, 0, 425000000, 425000000, 'posted', 'product', 8, 1, 23, 23, '{"5": 100}', 3, 3, NOW(), NOW()),
    (10004, 1001, 1002, '2024-01-15', '2024-01-15', 'Opening CIP081', 750000000, 0, 750000000, 750000000, 'posted', 'product', 8, 1, 23, 23, '{"11": 100}', 3, 3, NOW(), NOW()),
    (10005, 1001, 1002, '2024-01-15', '2024-01-15', 'Opening CIP082', 620000000, 0, 620000000, 620000000, 'posted', 'product', 8, 1, 23, 23, '{"12": 100}', 3, 3, NOW(), NOW()),
    (10006, 1001, 13, '2024-01-15', '2024-01-15', 'Opening Balance Contra', 0, 2645000000, -2645000000, -2645000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1002: January Additions (Jan 25)
    (10007, 1002, 1001, '2024-01-25', '2024-01-25', 'Construction CIP073', 180000000, 0, 180000000, 180000000, 'posted', 'product', 8, 1, 23, 23, '{"3": 100}', 3, 3, NOW(), NOW()),
    (10008, 1002, 1001, '2024-01-25', '2024-01-25', 'Equipment CIP091', 95000000, 0, 95000000, 95000000, 'posted', 'product', 8, 1, 23, 23, '{"21": 100}', 3, 3, NOW(), NOW()),
    (10009, 1002, 1001, '2024-01-25', '2024-01-25', 'Site Work CIP101', 120000000, 0, 120000000, 120000000, 'posted', 'product', 8, 1, 23, 23, '{"27": 100}', 3, 3, NOW(), NOW()),
    (10010, 1002, 13, '2024-01-25', '2024-01-25', 'Jan Contra', 0, 395000000, -395000000, -395000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1003: February Additions (Feb 10)
    (10011, 1003, 1001, '2024-02-10', '2024-02-10', 'Materials CIP071', 120000000, 0, 120000000, 120000000, 'posted', 'product', 8, 1, 23, 23, '{"1": 100}', 3, 3, NOW(), NOW()),
    (10012, 1003, 1001, '2024-02-10', '2024-02-10', 'Labor CIP076', 85000000, 0, 85000000, 85000000, 'posted', 'product', 8, 1, 23, 23, '{"6": 100}', 3, 3, NOW(), NOW()),
    (10013, 1003, 1001, '2024-02-10', '2024-02-10', 'Building CIP111', 145000000, 0, 145000000, 145000000, 'posted', 'product', 8, 1, 23, 23, '{"32": 100}', 3, 3, NOW(), NOW()),
    (10014, 1003, 1002, '2024-02-10', '2024-02-10', 'Utilities CIP083', 95000000, 0, 95000000, 95000000, 'posted', 'product', 8, 1, 23, 23, '{"13": 100}', 3, 3, NOW(), NOW()),
    (10015, 1003, 13, '2024-02-10', '2024-02-10', 'Feb Contra', 0, 445000000, -445000000, -445000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1004: February Equipment (Feb 28)
    (10016, 1004, 1001, '2024-02-28', '2024-02-28', 'Equipment CIP092', 155000000, 0, 155000000, 155000000, 'posted', 'product', 8, 1, 23, 23, '{"22": 100}', 3, 3, NOW(), NOW()),
    (10017, 1004, 1001, '2024-02-28', '2024-02-28', 'Packaging CIP093', 88000000, 0, 88000000, 88000000, 'posted', 'product', 8, 1, 23, 23, '{"23": 100}', 3, 3, NOW(), NOW()),
    (10018, 1004, 13, '2024-02-28', '2024-02-28', 'Feb Equip Contra', 0, 243000000, -243000000, -243000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1005: March Construction (Mar 15)
    (10019, 1005, 1001, '2024-03-15', '2024-03-15', 'Structure CIP074', 165000000, 0, 165000000, 165000000, 'posted', 'product', 8, 1, 23, 23, '{"4": 100}', 3, 3, NOW(), NOW()),
    (10020, 1005, 1001, '2024-03-15', '2024-03-15', 'Storage CIP077', 210000000, 0, 210000000, 210000000, 'posted', 'product', 8, 1, 23, 23, '{"7": 100}', 3, 3, NOW(), NOW()),
    (10021, 1005, 1001, '2024-03-15', '2024-03-15', 'Storage CIP078', 195000000, 0, 195000000, 195000000, 'posted', 'product', 8, 1, 23, 23, '{"8": 100}', 3, 3, NOW(), NOW()),
    (10022, 1005, 13, '2024-03-15', '2024-03-15', 'Mar Constr Contra', 0, 570000000, -570000000, -570000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1006: March Infrastructure (Mar 28)
    (10023, 1006, 1002, '2024-03-28', '2024-03-28', 'Drainage CIP084', 145000000, 0, 145000000, 145000000, 'posted', 'product', 8, 1, 23, 23, '{"14": 100}', 3, 3, NOW(), NOW()),
    (10024, 1006, 1002, '2024-03-28', '2024-03-28', 'Telecom CIP085', 122000000, 0, 122000000, 122000000, 'posted', 'product', 8, 1, 23, 23, '{"15": 100}', 3, 3, NOW(), NOW()),
    (10025, 1006, 1002, '2024-03-28', '2024-03-28', 'Fire System CIP086', 98000000, 0, 98000000, 98000000, 'posted', 'product', 8, 1, 23, 23, '{"16": 100}', 3, 3, NOW(), NOW()),
    (10026, 1006, 13, '2024-03-28', '2024-03-28', 'Mar Infra Contra', 0, 365000000, -365000000, -365000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1007: April Materials (Apr 10)
    (10027, 1007, 1001, '2024-04-10', '2024-04-10', 'Materials CIP071', 95000000, 0, 95000000, 95000000, 'posted', 'product', 8, 1, 23, 23, '{"1": 100}', 3, 3, NOW(), NOW()),
    (10028, 1007, 1001, '2024-04-10', '2024-04-10', 'Lab Equipment CIP079', 132000000, 0, 132000000, 132000000, 'posted', 'product', 8, 1, 23, 23, '{"9": 100}', 3, 3, NOW(), NOW()),
    (10029, 1007, 1001, '2024-04-10', '2024-04-10', 'Materials Handling CIP094', 78000000, 0, 78000000, 78000000, 'posted', 'product', 8, 1, 23, 23, '{"24": 100}', 3, 3, NOW(), NOW()),
    (10030, 1007, 13, '2024-04-10', '2024-04-10', 'Apr Mat Contra', 0, 305000000, -305000000, -305000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1008: April Labor (Apr 25)
    (10031, 1008, 1001, '2024-04-25', '2024-04-25', 'Labor CIP072', 110000000, 0, 110000000, 110000000, 'posted', 'product', 8, 1, 23, 23, '{"2": 100}', 3, 3, NOW(), NOW()),
    (10032, 1008, 1001, '2024-04-25', '2024-04-25', 'Labor CIP080', 92000000, 0, 92000000, 92000000, 'posted', 'product', 8, 1, 23, 23, '{"10": 100}', 3, 3, NOW(), NOW()),
    (10033, 1008, 1001, '2024-04-25', '2024-04-25', 'Labor CIP112', 135000000, 0, 135000000, 135000000, 'posted', 'product', 8, 1, 23, 23, '{"33": 100}', 3, 3, NOW(), NOW()),
    (10034, 1008, 13, '2024-04-25', '2024-04-25', 'Apr Labor Contra', 0, 337000000, -337000000, -337000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1009: May Mixed Projects (May 12)
    (10035, 1009, 1001, '2024-05-12', '2024-05-12', 'Mixed Costs', 150000000, 0, 150000000, 150000000, 'posted', 'product', 8, 1, 23, 23, '{"1": 40, "2": 30, "5": 30}', 3, 3, NOW(), NOW()),
    (10036, 1009, 1001, '2024-05-12', '2024-05-12', 'IT Infrastructure CIP095', 165000000, 0, 165000000, 165000000, 'posted', 'product', 8, 1, 23, 23, '{"25": 100}', 3, 3, NOW(), NOW()),
    (10037, 1009, 1002, '2024-05-12', '2024-05-12', 'Shared Infrastructure', 200000000, 0, 200000000, 200000000, 'posted', 'product', 8, 1, 23, 23, '{"11": 50, "12": 30, "13": 20}', 3, 3, NOW(), NOW()),
    (10038, 1009, 13, '2024-05-12', '2024-05-12', 'May Mixed Contra', 0, 515000000, -515000000, -515000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1010: May Development (May 28)
    (10039, 1010, 1001, '2024-05-28', '2024-05-28', 'Land Dev CIP102', 285000000, 0, 285000000, 285000000, 'posted', 'product', 8, 1, 23, 23, '{"28": 100}', 3, 3, NOW(), NOW()),
    (10040, 1010, 1001, '2024-05-28', '2024-05-28', 'Land Dev CIP103', 295000000, 0, 295000000, 295000000, 'posted', 'product', 8, 1, 23, 23, '{"29": 100}', 3, 3, NOW(), NOW()),
    (10041, 1010, 13, '2024-05-28', '2024-05-28', 'May Dev Contra', 0, 580000000, -580000000, -580000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1011: June Equipment Install (Jun 10)
    (10042, 1011, 1001, '2024-06-10', '2024-06-10', 'Automation CIP096', 245000000, 0, 245000000, 245000000, 'posted', 'product', 8, 1, 23, 23, '{"26": 100}', 3, 3, NOW(), NOW()),
    (10043, 1011, 1002, '2024-06-10', '2024-06-10', 'Sewage Treatment CIP087', 188000000, 0, 188000000, 188000000, 'posted', 'product', 8, 1, 23, 23, '{"17": 100}', 3, 3, NOW(), NOW()),
    (10044, 1011, 13, '2024-06-10', '2024-06-10', 'Jun Install Contra', 0, 433000000, -433000000, -433000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1012: June Transfer to Fixed Assets (Jun 25) - This is a DECREASE
    (10045, 1012, 1001, '2024-06-25', '2024-06-25', 'FA Transfer CIP073', 0, 180000000, -180000000, -180000000, 'posted', 'product', 8, 1, 23, 23, '{"3": 100}', 3, 3, NOW(), NOW()),
    (10046, 1012, 13, '2024-06-25', '2024-06-25', 'FA from CIP073', 180000000, 0, 180000000, 180000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1013: July Construction (Jul 8)
    (10047, 1013, 1001, '2024-07-08', '2024-07-08', 'Industrial Park CIP104', 420000000, 0, 420000000, 420000000, 'posted', 'product', 8, 1, 23, 23, '{"30": 100}', 3, 3, NOW(), NOW()),
    (10048, 1013, 1001, '2024-07-08', '2024-07-08', 'Industrial Park CIP105', 390000000, 0, 390000000, 390000000, 'posted', 'product', 8, 1, 23, 23, '{"31": 100}', 3, 3, NOW(), NOW()),
    (10049, 1013, 13, '2024-07-08', '2024-07-08', 'Jul Constr Contra', 0, 810000000, -810000000, -810000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1014: July Utilities (Jul 22)
    (10050, 1014, 1002, '2024-07-22', '2024-07-22', 'Security CIP088', 158000000, 0, 158000000, 158000000, 'posted', 'product', 8, 1, 23, 23, '{"18": 100}', 3, 3, NOW(), NOW()),
    (10051, 1014, 1002, '2024-07-22', '2024-07-22', 'HVAC CIP089', 225000000, 0, 225000000, 225000000, 'posted', 'product', 8, 1, 23, 23, '{"19": 100}', 3, 3, NOW(), NOW()),
    (10052, 1014, 1002, '2024-07-22', '2024-07-22', 'Gas Pipeline CIP090', 195000000, 0, 195000000, 195000000, 'posted', 'product', 8, 1, 23, 23, '{"20": 100}', 3, 3, NOW(), NOW()),
    (10053, 1014, 13, '2024-07-22', '2024-07-22', 'Jul Util Contra', 0, 578000000, -578000000, -578000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1015: August Facilities (Aug 5)
    (10054, 1015, 1001, '2024-08-05', '2024-08-05', 'Cold Storage CIP113', 520000000, 0, 520000000, 520000000, 'posted', 'product', 8, 1, 23, 23, '{"34": 100}', 3, 3, NOW(), NOW()),
    (10055, 1015, 1001, '2024-08-05', '2024-08-05', 'Distribution CIP114', 485000000, 0, 485000000, 485000000, 'posted', 'product', 8, 1, 23, 23, '{"35": 100}', 3, 3, NOW(), NOW()),
    (10056, 1015, 13, '2024-08-05', '2024-08-05', 'Aug Fac Contra', 0, 1005000000, -1005000000, -1005000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1016: August Site Work (Aug 20)
    (10057, 1016, 1001, '2024-08-20', '2024-08-20', 'Maintenance CIP115', 155000000, 0, 155000000, 155000000, 'posted', 'product', 8, 1, 23, 23, '{"36": 100}', 3, 3, NOW(), NOW()),
    (10058, 1016, 1002, '2024-08-20', '2024-08-20', 'Solar Power CIP121', 385000000, 0, 385000000, 385000000, 'posted', 'product', 8, 1, 23, 23, '{"37": 100}', 3, 3, NOW(), NOW()),
    (10059, 1016, 13, '2024-08-20', '2024-08-20', 'Aug Site Contra', 0, 540000000, -540000000, -540000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1017: September Projects (Sep 10)
    (10060, 1017, 1002, '2024-09-10', '2024-09-10', 'Environmental CIP122', 275000000, 0, 275000000, 275000000, 'posted', 'product', 8, 1, 23, 23, '{"38": 100}', 3, 3, NOW(), NOW()),
    (10061, 1017, 1001, '2024-09-10', '2024-09-10', 'Dormitory CIP123', 315000000, 0, 315000000, 315000000, 'posted', 'product', 8, 1, 23, 23, '{"39": 100}', 3, 3, NOW(), NOW()),
    (10062, 1017, 13, '2024-09-10', '2024-09-10', 'Sep Proj Contra', 0, 590000000, -590000000, -590000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1018: September Infrastructure (Sep 25)
    (10063, 1018, 1001, '2024-09-25', '2024-09-25', 'Recreation CIP124', 185000000, 0, 185000000, 185000000, 'posted', 'product', 8, 1, 23, 23, '{"40": 100}', 3, 3, NOW(), NOW()),
    (10064, 1018, 1002, '2024-09-25', '2024-09-25', 'Road Network CIP081', 265000000, 0, 265000000, 265000000, 'posted', 'product', 8, 1, 23, 23, '{"11": 100}', 3, 3, NOW(), NOW()),
    (10065, 1018, 13, '2024-09-25', '2024-09-25', 'Sep Infra Contra', 0, 450000000, -450000000, -450000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW()),

    -- Move 1019: October Multi-Project (Oct 8) - Mixed distributions
    (10066, 1019, 1001, '2024-10-08', '2024-10-08', 'Multi-Building Work', 450000000, 0, 450000000, 450000000, 'posted', 'product', 8, 1, 23, 23, '{"1": 25, "5": 25, "32": 25, "33": 25}', 3, 3, NOW(), NOW()),
    (10067, 1019, 1002, '2024-10-08', '2024-10-08', 'Multi-Infrastructure Work', 380000000, 0, 380000000, 380000000, 'posted', 'product', 8, 1, 23, 23, '{"11": 30, "12": 30, "37": 40}', 3, 3, NOW(), NOW()),
    (10068, 1019, 13, '2024-10-08', '2024-10-08', 'Oct Multi Contra', 0, 830000000, -830000000, -830000000, 'posted', 'product', 8, 1, 23, 23, NULL, 3, 3, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Update sequence for account_move_line
SELECT setval('account_move_line_id_seq', (SELECT MAX(id) FROM account_move_line));

-- Summary of what was created:
-- Step 1: Budget Categories: 5 (Construction, Infrastructure, Equipment, Development, Facilities)
-- Step 2: Budget Codes: 10 (INV-01-01 through INV-05-02)
-- Step 3: CIP/WIP Accounts: 2 (2411, 2412)
-- Step 4: Analytic Accounts (Budget Code Accounts): 40 (CIP071-CIP124 covering Construction, Infrastructure, Equipment, Development, and Facilities)
-- Step 5: Development Projects: 15 (PRJ-001 through PRJ-015 representing actual project entities)
-- Step 6: Journal Entries (Account Moves): 19 entries with development_project_id linkage
-- Step 7: Journal Items (Account Move Lines): 68 lines with analytic distribution
--
-- Date Range: January 2024 to October 2024
-- Coverage: All transactions properly linked to development projects
-- Total CIP Value: ~11+ billion VND across all projects
-- Features:
--   - Opening balances for major projects
--   - Period additions across multiple projects
--   - One transfer to fixed assets (decrease transaction)
--   - Mixed analytic distributions (multiple budget codes per line)
--   - Full integration: Development Projects -> Journal Entries -> Journal Items -> Analytic Accounts (Budget Codes)
--
-- The data structure ensures:
-- 1. Each Journal Entry (account_move) is linked to a Development Project
-- 2. Each Journal Item (account_move_line) inherits the project from its parent move
-- 3. Each Journal Item is distributed across Budget Codes via analytic_distribution
-- 4. The CIP WIP report can group by Project and show Budget Code details

SELECT 'Dummy data created successfully with proper project linkage!' as status;
