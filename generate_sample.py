"""Generate a sample capability model Excel file for testing visualize.py."""
import pandas as pd

rows = [
    # L1 - Finance tier
    {"capability ID": "F1",    "Capability name": "Finance",              "tier": "Corporate",   " capability description": "All financial management capabilities",             "capability level": 1, "capability parent name ": "",              "capability parent id": "",   "capability type": "Domain",    "source": "Internal"},
    # L2 - Finance children
    {"capability ID": "F1.1",  "Capability name": "Budgeting",            "tier": "Corporate",   " capability description": "Planning and managing budgets",                    "capability level": 2, "capability parent name ": "Finance",       "capability parent id": "F1",  "capability type": "Function",  "source": "Finance Dept"},
    {"capability ID": "F1.2",  "Capability name": "Financial Reporting",  "tier": "Corporate",   " capability description": "Producing financial statements and reports",       "capability level": 2, "capability parent name ": "Finance",       "capability parent id": "F1",  "capability type": "Function",  "source": "Finance Dept"},
    {"capability ID": "F1.3",  "Capability name": "Accounts Payable",     "tier": "Corporate",   " capability description": "Managing outgoing payments to vendors",            "capability level": 2, "capability parent name ": "Finance",       "capability parent id": "F1",  "capability type": "Function",  "source": "Finance Dept"},
    # L3 - Budgeting children
    {"capability ID": "F1.1.1","Capability name": "Budget Planning",      "tier": "Corporate",   " capability description": "Defining annual budget targets",                   "capability level": 3, "capability parent name ": "Budgeting",     "capability parent id": "F1.1","capability type": "Activity",  "source": "Finance Dept"},
    {"capability ID": "F1.1.2","Capability name": "Budget Tracking",      "tier": "Corporate",   " capability description": "Monitoring spend against approved budgets",        "capability level": 3, "capability parent name ": "Budgeting",     "capability parent id": "F1.1","capability type": "Activity",  "source": "Finance Dept"},

    # L1 - Operations tier
    {"capability ID": "O1",    "Capability name": "Operations",           "tier": "Business",    " capability description": "Core operational delivery capabilities",            "capability level": 1, "capability parent name ": "",              "capability parent id": "",   "capability type": "Domain",    "source": "Internal"},
    # L2 - Operations children
    {"capability ID": "O1.1",  "Capability name": "Supply Chain",         "tier": "Business",    " capability description": "Managing the flow of goods and materials",         "capability level": 2, "capability parent name ": "Operations",    "capability parent id": "O1",  "capability type": "Function",  "source": "Ops Dept"},
    {"capability ID": "O1.2",  "Capability name": "Quality Management",   "tier": "Business",    " capability description": "Ensuring products and services meet standards",     "capability level": 2, "capability parent name ": "Operations",    "capability parent id": "O1",  "capability type": "Function",  "source": "Ops Dept"},
    # L3 - Supply Chain children
    {"capability ID": "O1.1.1","Capability name": "Procurement",          "tier": "Business",    " capability description": "Sourcing and purchasing goods and services",       "capability level": 3, "capability parent name ": "Supply Chain",   "capability parent id": "O1.1","capability type": "Activity",  "source": "Ops Dept"},
    {"capability ID": "O1.1.2","Capability name": "Inventory Management", "tier": "Business",    " capability description": "Tracking and controlling stock levels",             "capability level": 3, "capability parent name ": "Supply Chain",   "capability parent id": "O1.1","capability type": "Activity",  "source": "Ops Dept"},

    # L1 - HR tier
    {"capability ID": "H1",    "Capability name": "Human Resources",      "tier": "Corporate",   " capability description": "People management and development capabilities",    "capability level": 1, "capability parent name ": "",              "capability parent id": "",   "capability type": "Domain",    "source": "Internal"},
    # L2 - HR children
    {"capability ID": "H1.1",  "Capability name": "Talent Acquisition",   "tier": "Corporate",   " capability description": "Recruiting and onboarding new employees",           "capability level": 2, "capability parent name ": "Human Resources","capability parent id": "H1",  "capability type": "Function",  "source": "HR Dept"},
    {"capability ID": "H1.2",  "Capability name": "Learning & Development","tier": "Corporate",  " capability description": "Training and growing employee skills",              "capability level": 2, "capability parent name ": "Human Resources","capability parent id": "H1",  "capability type": "Function",  "source": "HR Dept"},
    # L3 - Talent Acquisition children
    {"capability ID": "H1.1.1","Capability name": "Job Posting",          "tier": "Corporate",   " capability description": "Advertising open positions across channels",        "capability level": 3, "capability parent name ": "Talent Acquisition","capability parent id": "H1.1","capability type": "Activity", "source": "HR Dept"},
    {"capability ID": "H1.1.2","Capability name": "Candidate Screening",  "tier": "Corporate",   " capability description": "Reviewing and shortlisting applicants",             "capability level": 3, "capability parent name ": "Talent Acquisition","capability parent id": "H1.1","capability type": "Activity", "source": "HR Dept"},
]

df = pd.DataFrame(rows)
output_file = "sample_capabilities.xlsx"
df.to_excel(output_file, index=False)
print(f"Created {output_file} with {len(df)} capability rows.")
