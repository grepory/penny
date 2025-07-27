-- Penny Home Renovation Expense Tracking Database Schema
-- SQLite database schema with proper relationships, indexing, and constraints

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Vendors table
CREATE TABLE vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    tax_id TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vendors
CREATE INDEX idx_vendors_name ON vendors(name);
CREATE INDEX idx_vendors_tax_id ON vendors(tax_id);

-- Projects table
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_type TEXT NOT NULL CHECK (project_type IN (
        'kitchen_remodel', 'bathroom_remodel', 'basement_renovation', 'addition',
        'roof_replacement', 'flooring', 'painting', 'electrical_upgrade',
        'plumbing_upgrade', 'hvac_installation', 'siding_replacement',
        'window_replacement', 'deck_construction', 'driveway', 'landscaping',
        'general_maintenance', 'other'
    )),
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    location TEXT,
    status TEXT DEFAULT 'planning' CHECK (status IN ('planning', 'in_progress', 'completed', 'on_hold')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for projects
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_type ON projects(project_type);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_dates ON projects(start_date, end_date);

-- Expense category mappings table
CREATE TABLE expense_categories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL CHECK (category IN (
        'materials_lumber', 'materials_concrete', 'materials_steel', 'materials_stone',
        'materials_tile', 'materials_flooring', 'materials_insulation', 'materials_roofing',
        'materials_siding', 'materials_windows', 'materials_doors', 'paint_interior',
        'paint_exterior', 'paint_supplies', 'electrical_fixtures', 'electrical_wiring',
        'electrical_outlets', 'plumbing_fixtures', 'plumbing_pipes', 'plumbing_fittings',
        'hvac_units', 'hvac_ductwork', 'hvac_maintenance', 'appliances_kitchen',
        'appliances_laundry', 'appliances_other', 'tools_power', 'tools_hand',
        'tools_rental', 'labor_contractor', 'labor_electrician', 'labor_plumber',
        'labor_hvac', 'labor_painter', 'labor_flooring', 'labor_general',
        'permits_building', 'permits_electrical', 'permits_plumbing',
        'delivery_materials', 'delivery_appliances', 'waste_disposal', 'miscellaneous'
    )),
    subcategory TEXT,
    description TEXT,
    keywords TEXT, -- JSON array of keywords
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for expense categories
CREATE INDEX idx_expense_categories_category ON expense_categories(category);
CREATE INDEX idx_expense_categories_active ON expense_categories(is_active);

-- Documents table (extends the existing document system)
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed BOOLEAN DEFAULT FALSE
);

-- Financial documents table (links to documents table)
CREATE TABLE financial_documents (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN (
        'invoice', 'receipt', 'estimate', 'contract', 'purchase_order', 'warranty', 'other'
    )),
    
    -- Vendor information
    vendor_id TEXT,
    vendor_name TEXT NOT NULL,
    vendor_address TEXT,
    vendor_phone TEXT,
    vendor_email TEXT,
    vendor_tax_id TEXT,
    
    -- Document details
    invoice_number TEXT,
    invoice_date DATE,
    purchase_order_number TEXT,
    
    -- Financial totals
    subtotal DECIMAL(15,2),
    total_tax DECIMAL(15,2),
    total_amount DECIMAL(15,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    
    -- Project association
    project_id TEXT,
    
    -- Additional metadata
    notes TEXT,
    tags TEXT, -- JSON array of tags
    
    -- Processing metadata
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    manually_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Create indexes for financial documents
CREATE INDEX idx_financial_docs_document_id ON financial_documents(document_id);
CREATE INDEX idx_financial_docs_vendor_id ON financial_documents(vendor_id);
CREATE INDEX idx_financial_docs_project_id ON financial_documents(project_id);
CREATE INDEX idx_financial_docs_type ON financial_documents(document_type);
CREATE INDEX idx_financial_docs_date ON financial_documents(invoice_date);
CREATE INDEX idx_financial_docs_amount ON financial_documents(total_amount);
CREATE INDEX idx_financial_docs_vendor_name ON financial_documents(vendor_name);

-- Line items table
CREATE TABLE line_items (
    id TEXT PRIMARY KEY,
    financial_document_id TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(15,4) NOT NULL CHECK (quantity >= 0),
    unit_price DECIMAL(15,2) NOT NULL CHECK (unit_price >= 0),
    unit_of_measure TEXT,
    line_total DECIMAL(15,2) NOT NULL CHECK (line_total >= 0),
    category TEXT CHECK (category IN (
        'materials_lumber', 'materials_concrete', 'materials_steel', 'materials_stone',
        'materials_tile', 'materials_flooring', 'materials_insulation', 'materials_roofing',
        'materials_siding', 'materials_windows', 'materials_doors', 'paint_interior',
        'paint_exterior', 'paint_supplies', 'electrical_fixtures', 'electrical_wiring',
        'electrical_outlets', 'plumbing_fixtures', 'plumbing_pipes', 'plumbing_fittings',
        'hvac_units', 'hvac_ductwork', 'hvac_maintenance', 'appliances_kitchen',
        'appliances_laundry', 'appliances_other', 'tools_power', 'tools_hand',
        'tools_rental', 'labor_contractor', 'labor_electrician', 'labor_plumber',
        'labor_hvac', 'labor_painter', 'labor_flooring', 'labor_general',
        'permits_building', 'permits_electrical', 'permits_plumbing',
        'delivery_materials', 'delivery_appliances', 'waste_disposal', 'miscellaneous'
    )),
    subcategory TEXT,
    product_code TEXT,
    brand TEXT,
    model TEXT,
    project_id TEXT,
    notes TEXT,
    
    -- Tax information
    tax_rate DECIMAL(8,6) CHECK (tax_rate >= 0 AND tax_rate <= 1),
    tax_amount DECIMAL(15,2) CHECK (tax_amount >= 0),
    tax_type TEXT,
    tax_exempt BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (financial_document_id) REFERENCES financial_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Create indexes for line items
CREATE INDEX idx_line_items_financial_doc ON line_items(financial_document_id);
CREATE INDEX idx_line_items_category ON line_items(category);
CREATE INDEX idx_line_items_project_id ON line_items(project_id);
CREATE INDEX idx_line_items_description ON line_items(description);
CREATE INDEX idx_line_items_brand ON line_items(brand);
CREATE INDEX idx_line_items_amount ON line_items(line_total);

-- Payment information table
CREATE TABLE payment_info (
    id TEXT PRIMARY KEY,
    financial_document_id TEXT NOT NULL,
    payment_method TEXT CHECK (payment_method IN (
        'cash', 'check', 'credit_card', 'debit_card', 'bank_transfer', 'financing', 'store_credit', 'other'
    )),
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN (
        'pending', 'paid', 'partial', 'overdue', 'cancelled'
    )),
    due_date DATE,
    paid_date DATE,
    paid_amount DECIMAL(15,2) CHECK (paid_amount >= 0),
    payment_reference TEXT,
    discount_amount DECIMAL(15,2) CHECK (discount_amount >= 0),
    late_fee DECIMAL(15,2) CHECK (late_fee >= 0),
    notes TEXT,
    
    FOREIGN KEY (financial_document_id) REFERENCES financial_documents(id) ON DELETE CASCADE
);

-- Create indexes for payment info
CREATE INDEX idx_payment_info_financial_doc ON payment_info(financial_document_id);
CREATE INDEX idx_payment_info_status ON payment_info(payment_status);
CREATE INDEX idx_payment_info_method ON payment_info(payment_method);
CREATE INDEX idx_payment_info_due_date ON payment_info(due_date);

-- Auto-categorization rules table
CREATE TABLE auto_categorization_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vendor_patterns TEXT, -- JSON array
    description_patterns TEXT, -- JSON array
    amount_min DECIMAL(15,2),
    amount_max DECIMAL(15,2),
    category TEXT NOT NULL CHECK (category IN (
        'materials_lumber', 'materials_concrete', 'materials_steel', 'materials_stone',
        'materials_tile', 'materials_flooring', 'materials_insulation', 'materials_roofing',
        'materials_siding', 'materials_windows', 'materials_doors', 'paint_interior',
        'paint_exterior', 'paint_supplies', 'electrical_fixtures', 'electrical_wiring',
        'electrical_outlets', 'plumbing_fixtures', 'plumbing_pipes', 'plumbing_fittings',
        'hvac_units', 'hvac_ductwork', 'hvac_maintenance', 'appliances_kitchen',
        'appliances_laundry', 'appliances_other', 'tools_power', 'tools_hand',
        'tools_rental', 'labor_contractor', 'labor_electrician', 'labor_plumber',
        'labor_hvac', 'labor_painter', 'labor_flooring', 'labor_general',
        'permits_building', 'permits_electrical', 'permits_plumbing',
        'delivery_materials', 'delivery_appliances', 'waste_disposal', 'miscellaneous'
    )),
    subcategory TEXT,
    project_id TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_threshold REAL DEFAULT 0.8 CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Create indexes for auto-categorization rules
CREATE INDEX idx_auto_cat_rules_active ON auto_categorization_rules(is_active);
CREATE INDEX idx_auto_cat_rules_priority ON auto_categorization_rules(priority);
CREATE INDEX idx_auto_cat_rules_category ON auto_categorization_rules(category);

-- Categorization suggestions table
CREATE TABLE categorization_suggestions (
    id TEXT PRIMARY KEY,
    line_item_id TEXT NOT NULL,
    suggested_category TEXT NOT NULL CHECK (suggested_category IN (
        'materials_lumber', 'materials_concrete', 'materials_steel', 'materials_stone',
        'materials_tile', 'materials_flooring', 'materials_insulation', 'materials_roofing',
        'materials_siding', 'materials_windows', 'materials_doors', 'paint_interior',
        'paint_exterior', 'paint_supplies', 'electrical_fixtures', 'electrical_wiring',
        'electrical_outlets', 'plumbing_fixtures', 'plumbing_pipes', 'plumbing_fittings',
        'hvac_units', 'hvac_ductwork', 'hvac_maintenance', 'appliances_kitchen',
        'appliances_laundry', 'appliances_other', 'tools_power', 'tools_hand',
        'tools_rental', 'labor_contractor', 'labor_electrician', 'labor_plumber',
        'labor_hvac', 'labor_painter', 'labor_flooring', 'labor_general',
        'permits_building', 'permits_electrical', 'permits_plumbing',
        'delivery_materials', 'delivery_appliances', 'waste_disposal', 'miscellaneous'
    )),
    suggested_subcategory TEXT,
    suggested_project_id TEXT,
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT NOT NULL,
    similar_items TEXT, -- JSON array of similar item IDs
    accepted BOOLEAN,
    user_category TEXT,
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (line_item_id) REFERENCES line_items(id) ON DELETE CASCADE,
    FOREIGN KEY (suggested_project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Create indexes for categorization suggestions
CREATE INDEX idx_cat_suggestions_line_item ON categorization_suggestions(line_item_id);
CREATE INDEX idx_cat_suggestions_accepted ON categorization_suggestions(accepted);
CREATE INDEX idx_cat_suggestions_confidence ON categorization_suggestions(confidence);

-- Budget alerts table
CREATE TABLE budget_alerts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    category TEXT CHECK (category IN (
        'materials_lumber', 'materials_concrete', 'materials_steel', 'materials_stone',
        'materials_tile', 'materials_flooring', 'materials_insulation', 'materials_roofing',
        'materials_siding', 'materials_windows', 'materials_doors', 'paint_interior',
        'paint_exterior', 'paint_supplies', 'electrical_fixtures', 'electrical_wiring',
        'electrical_outlets', 'plumbing_fixtures', 'plumbing_pipes', 'plumbing_fittings',
        'hvac_units', 'hvac_ductwork', 'hvac_maintenance', 'appliances_kitchen',
        'appliances_laundry', 'appliances_other', 'tools_power', 'tools_hand',
        'tools_rental', 'labor_contractor', 'labor_electrician', 'labor_plumber',
        'labor_hvac', 'labor_painter', 'labor_flooring', 'labor_general',
        'permits_building', 'permits_electrical', 'permits_plumbing',
        'delivery_materials', 'delivery_appliances', 'waste_disposal', 'miscellaneous'
    )),
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'budget_exceeded', 'budget_warning', 'unusual_spending', 'payment_due'
    )),
    threshold_percentage REAL CHECK (threshold_percentage >= 0 AND threshold_percentage <= 1),
    threshold_amount DECIMAL(15,2) CHECK (threshold_amount >= 0),
    current_amount DECIMAL(15,2) NOT NULL CHECK (current_amount >= 0),
    budget_amount DECIMAL(15,2),
    percentage_used REAL CHECK (percentage_used >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    message TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create indexes for budget alerts
CREATE INDEX idx_budget_alerts_project ON budget_alerts(project_id);
CREATE INDEX idx_budget_alerts_category ON budget_alerts(category);
CREATE INDEX idx_budget_alerts_active ON budget_alerts(is_active);
CREATE INDEX idx_budget_alerts_acknowledged ON budget_alerts(is_acknowledged);
CREATE INDEX idx_budget_alerts_severity ON budget_alerts(severity);

-- Query logs table (for natural language query tracking)
CREATE TABLE query_logs (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_intent TEXT CHECK (query_intent IN (
        'expense_search', 'project_summary', 'category_analysis', 'time_analysis', 'vendor_analysis'
    )),
    entities TEXT, -- JSON object
    filters TEXT, -- JSON object
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    execution_time REAL NOT NULL,
    data_points INTEGER DEFAULT 0,
    natural_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for query logs
CREATE INDEX idx_query_logs_intent ON query_logs(query_intent);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX idx_query_logs_confidence ON query_logs(confidence);

-- Views for common queries

-- Project spending summary view
CREATE VIEW project_spending_summary AS
SELECT 
    p.id,
    p.name,
    p.project_type,
    p.budget,
    p.status,
    COALESCE(SUM(fd.total_amount), 0) as total_spent,
    COALESCE(p.budget - SUM(fd.total_amount), p.budget) as budget_remaining,
    CASE 
        WHEN p.budget > 0 THEN (SUM(fd.total_amount) / p.budget) * 100
        ELSE NULL 
    END as budget_utilization_percent,
    COUNT(fd.id) as document_count,
    MIN(fd.invoice_date) as first_expense_date,
    MAX(fd.invoice_date) as last_expense_date
FROM projects p
LEFT JOIN financial_documents fd ON p.id = fd.project_id
GROUP BY p.id, p.name, p.project_type, p.budget, p.status;

-- Category spending summary view
CREATE VIEW category_spending_summary AS
SELECT 
    li.category,
    COUNT(li.id) as item_count,
    SUM(li.line_total) as total_spent,
    AVG(li.line_total) as average_amount,
    COUNT(DISTINCT li.financial_document_id) as document_count,
    COUNT(DISTINCT fd.vendor_id) as vendor_count,
    COUNT(DISTINCT li.project_id) as project_count,
    MIN(fd.invoice_date) as first_purchase_date,
    MAX(fd.invoice_date) as last_purchase_date
FROM line_items li
JOIN financial_documents fd ON li.financial_document_id = fd.id
WHERE li.category IS NOT NULL
GROUP BY li.category;

-- Vendor spending summary view
CREATE VIEW vendor_spending_summary AS
SELECT 
    v.id,
    v.name,
    COUNT(fd.id) as transaction_count,
    SUM(fd.total_amount) as total_spent,
    AVG(fd.total_amount) as average_transaction,
    COUNT(DISTINCT fd.project_id) as project_count,
    MIN(fd.invoice_date) as first_transaction_date,
    MAX(fd.invoice_date) as last_transaction_date
FROM vendors v
JOIN financial_documents fd ON v.id = fd.vendor_id
GROUP BY v.id, v.name;

-- Monthly spending summary view
CREATE VIEW monthly_spending_summary AS
SELECT 
    strftime('%Y-%m', fd.invoice_date) as month,
    COUNT(fd.id) as transaction_count,
    SUM(fd.total_amount) as total_spent,
    AVG(fd.total_amount) as average_transaction,
    COUNT(DISTINCT fd.vendor_id) as vendor_count,
    COUNT(DISTINCT fd.project_id) as project_count
FROM financial_documents fd
WHERE fd.invoice_date IS NOT NULL
GROUP BY strftime('%Y-%m', fd.invoice_date)
ORDER BY month;

-- Triggers for updating timestamps

-- Update timestamps on vendors
CREATE TRIGGER update_vendors_timestamp 
AFTER UPDATE ON vendors
BEGIN
    UPDATE vendors SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps on projects
CREATE TRIGGER update_projects_timestamp 
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps on financial documents
CREATE TRIGGER update_financial_documents_timestamp 
AFTER UPDATE ON financial_documents
BEGIN
    UPDATE financial_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to automatically create vendor records from financial documents
CREATE TRIGGER auto_create_vendor
AFTER INSERT ON financial_documents
WHEN NEW.vendor_id IS NULL AND NEW.vendor_name IS NOT NULL
BEGIN
    INSERT OR IGNORE INTO vendors (id, name, address, phone, email, tax_id)
    VALUES (
        lower(hex(randomblob(16))),
        NEW.vendor_name,
        NEW.vendor_address,
        NEW.vendor_phone,
        NEW.vendor_email,
        NEW.vendor_tax_id
    );
    
    UPDATE financial_documents 
    SET vendor_id = (SELECT id FROM vendors WHERE name = NEW.vendor_name LIMIT 1)
    WHERE id = NEW.id;
END;

-- Validation trigger for line item totals
CREATE TRIGGER validate_line_item_total
BEFORE INSERT ON line_items
BEGIN
    SELECT CASE
        WHEN ABS(NEW.line_total - (NEW.quantity * NEW.unit_price)) > 0.01 THEN
            RAISE(ABORT, 'Line total must equal quantity * unit_price')
    END;
END;