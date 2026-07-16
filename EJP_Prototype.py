"""
Modern ICER Drug Price Calculator
A beautiful, intuitive Shiny app for calculating economically justifiable drug pricing
based on ICER thresholds and cost-effectiveness analysis.
"""

import sys
import subprocess

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        sys.exit(1)

# Required packages
required_packages = [
    'shiny',
    'pandas',
    'numpy',
    'plotly',
    'htmltools',
    'matplotlib',
    'openpyxl'
]

# Check and install missing packages
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        install_package(package)
try:
    from shiny import App, ui, render, reactive
except ImportError:
    import subprocess
    import sys
    print("Installing Shiny for Python...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "shiny"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error installing shiny: {result.stderr}")
        raise ImportError("Failed to install shiny. Check your pip configuration and internet connection.")
    print("Shiny installed successfully!")
    from shiny import App, ui, render, reactive
from shiny.types import ImgData
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import io

from icer_core import (
    ICERScenario,
    calculate_scenario_results,
    validate_inputs,
    compare_scenarios,
    create_icer_discount_plot
)


# Modern color palette - Professional healthcare/pharma aesthetic
COLORS = {
    'primary': '#2563eb',      # Blue
    'secondary': "#8054E6",    # Purple
    'success': '#10b981',      # Green
    'warning': '#f59e0b',      # Amber
    'danger': '#ef4444',       # Red
    'info': '#06b6d4',         # Cyan
    'light': '#f8fafc',        # Light gray
    'dark': '#1e293b',         # Dark slate
    'border': '#e2e8f0'        # Border gray
}


# Custom CSS for modern, clean design
app_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{
    box-sizing: border-box;
}}

* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

html, body {{
    max-width: 100%;
    overflow-x: hidden;
}}

body {{
    background: linear-gradient(135deg, #083458 0%, #0a4d7a 100%);
    min-height: 100vh;
}}

.app-header-inner {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    padding: 0 2rem;
}}

.app-logo {{
    height: 70px;
    width: 70px;
    flex-shrink: 0;
}}

.app-layout {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 1.5rem;
    display: flex;
    gap: 1.5rem;
}}

.app-sidebar {{
    width: 260px;
    flex-shrink: 0;
}}

.app-sidebar-card {{
    position: sticky;
    top: 1rem;
}}

.cost-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1.25rem;
    padding: 1.25rem 1.5rem;
    align-items: end;
}}

.ref-cost-span {{
    grid-column: 1 / span 3;
    align-self: end;
}}

.ref-cost-input {{
    max-width: 280px;
}}

.btn-calculate {{
    font-size: 1.1rem;
    padding: 0.75rem 2.5rem;
}}

.table-scroll {{
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}}

.app-header {{
    background: white;
    padding: 1.5rem 0;
    margin-bottom: 0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.app-header h1 {{
    color: #083458;
    font-weight: 600;
    font-size: 2.5rem;
    margin: 0 0 0.5rem 0;
}}

.app-header p {{
    color: #64748b;
    font-size: 1.1rem;
    margin: 0;
    font-weight: 400;
}}

.card {{
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
    border: 1px solid {COLORS['border']};
}}

.card-header {{
    font-size: 1.25rem;
    font-weight: 600;
    color: {COLORS['dark']};
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid {COLORS['border']};
}}

.input-group {{
    margin-bottom: 1.5rem;
}}

.input-group label {{
    display: block;
    font-weight: 500;
    color: {COLORS['dark']};
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}}

.input-group input, .input-group select {{
    width: 100%;
    padding: 0.75rem;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    font-size: 1rem;
    transition: all 0.2s;
}}

.input-group .shiny-input-container {{
    width: 100%;
    max-width: 100%;
}}

.input-group input:focus, .input-group select:focus {{
    outline: none;
    border-color: {COLORS['primary']};
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}}

.help-text {{
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 0.25rem;
}}

.tooltip-icon {{
    display: inline-block;
    width: 18px;
    height: 18px;
    background: {COLORS['info']};
    color: white;
    border-radius: 50%;
    text-align: center;
    line-height: 18px;
    font-size: 12px;
    font-weight: bold;
    margin-left: 0.5rem;
    cursor: help;
}}

.btn {{
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-block;
    text-align: center;
}}

.btn-primary {{
    background: {COLORS['primary']};
    color: white;
}}

.btn-primary:hover {{
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}}

.btn-success {{
    background: {COLORS['success']};
    color: white;
}}

.btn-success:hover {{
    background: #059669;
}}

.btn-secondary {{
    background: {COLORS['secondary']};
    color: white;
}}

.btn-danger {{
    background: {COLORS['danger']};
    color: white;
}}

.btn-danger:hover {{
    background: #dc2626;
}}

.result-card {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
    color: white;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}}

.result-primary {{
    font-size: 3rem;
    font-weight: 700;
    margin: 1rem 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}

.result-label {{
    font-size: 1.1rem;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
}}

.metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}}

.metric-card {{
    background: {COLORS['light']};
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 4px solid {COLORS['primary']};
}}

.metric-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {COLORS['dark']};
    margin: 0.5rem 0;
}}

.metric-label {{
    font-size: 0.9rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}}

.badge {{
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
}}

.badge-success {{
    background: {COLORS['success']};
    color: white;
}}

.badge-danger {{
    background: {COLORS['danger']};
    color: white;
}}

.scenario-list {{
    max-height: 400px;
    overflow-y: auto;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 0.5rem;
}}

.scenario-item {{
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    border: 2px solid transparent;
}}

.scenario-item:hover {{
    background: {COLORS['light']};
    border-color: {COLORS['primary']};
}}

.scenario-item.active {{
    background: {COLORS['primary']};
    color: white;
}}

.alert {{
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 4px solid;
}}

.alert-danger {{
    background: #fef2f2;
    border-color: {COLORS['danger']};
    color: #991b1b;
}}

.alert-warning {{
    background: #fffbeb;
    border-color: {COLORS['warning']};
    color: #92400e;
}}

.alert-info {{
    background: #f0f9ff;
    border-color: {COLORS['info']};
    color: #075985;
}}

.comparison-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}}

.comparison-table th {{
    background: {COLORS['light']};
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid {COLORS['border']};
}}

.comparison-table td {{
    padding: 1rem;
    border-bottom: 1px solid {COLORS['border']};
}}

.comparison-table tr:hover {{
    background: {COLORS['light']};
}}

/* ── Tablet ────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {{
    .app-layout {{
        flex-direction: column;
    }}

    .app-sidebar {{
        width: 100%;
    }}

    .app-sidebar-card {{
        position: static;
    }}

    .cost-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}

    .ref-cost-span {{
        grid-column: 1 / -1;
    }}
}}

/* ── Mobile ────────────────────────────────────────────────────────── */
@media (max-width: 640px) {{
    .app-layout {{
        padding: 1rem;
        gap: 1rem;
    }}

    .app-header-inner {{
        flex-direction: column;
        gap: 0.5rem;
        padding: 0 1rem;
        text-align: center;
    }}

    .app-logo {{
        height: 50px;
        width: 50px;
    }}

    .app-header h1 {{
        font-size: 1.6rem;
    }}

    .app-header p {{
        font-size: 0.9rem;
    }}

    .card {{
        padding: 1rem;
    }}

    .card-header {{
        font-size: 1.1rem;
    }}

    .cost-grid {{
        grid-template-columns: 1fr;
        padding: 1rem;
    }}

    .ref-cost-input {{
        max-width: 100%;
    }}

    .metric-grid {{
        grid-template-columns: 1fr;
    }}

    .result-primary {{
        font-size: 2rem;
    }}

    .btn-calculate {{
        width: 100%;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
    }}

    .comparison-table th,
    .comparison-table td {{
        padding: 0.6rem;
        font-size: 0.85rem;
    }}
}}
"""


# App UI
app_ui = ui.page_fluid(
    ui.tags.style(app_css),
    ui.tags.head(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        ui.tags.link(rel="icon", type="image/jpg", href="SYMMETRON symbol.jpg")
    ),

    # Header
    ui.div(
        {"class": "app-header"},
        ui.div(
            {"class": "app-header-inner"},
            ui.img(
                src="symmetron-wordmark.svg",
                class_="app-logo",
                style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
            ),
            ui.div(
                {"style": "text-align: left;"},
                ui.h1("PriceLens", style="margin: 0; letter-spacing: -0.5px;"),
                ui.p("Calculate economically justifiable drug pricing based on cost-effectiveness thresholds", style="margin: 0.5rem 0 0 0;")
            )
        )
    ),

    # Main layout with sidebar
    ui.div(
        {"class": "app-layout"},

        # Left Sidebar - Scenario Management
        ui.div(
            {"class": "app-sidebar"},
            ui.div(
                {"class": "card app-sidebar-card"},
                ui.div(
                    {"class": "card-header"},
                    "Scenario Management"
                ),
                ui.div(
                    {"style": "padding: 1rem;"},
                    
                    # Drug Names and Currency Section
                    ui.div(
                        {"style": "margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0;"},
                        ui.div(
                            {"style": "margin-bottom: 0.75rem; font-weight: 500; color: #475569;"},
                            "Study Parameters"
                        ),
                        ui.div(
                            {"class": "input-group", "style": "margin-bottom: 0.5rem;"},
                            ui.tags.label("Intervention Drug Name"),
                            ui.input_text(
                                "intervention_drug_name",
                                None,
                                placeholder="e.g., Drug A",
                                value="New Drug",
                                width="100%"
                            )
                        ),
                        ui.div(
                            {"class": "input-group", "style": "margin-bottom: 0.5rem;"},
                            ui.tags.label("Comparator Name"),
                            ui.input_text(
                                "comparator_name",
                                None,
                                placeholder="e.g., Standard Care",
                                value="Reference Drug",
                                width="100%"
                            )
                        ),
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Currency"),
                            ui.input_select(
                                "currency_select",
                                None,
                                choices={"£": "£ (GBP)", "$": "$ (USD)", "€": "€ (EUR)"},
                                selected="£",
                                width="100%"
                            )
                        )
                    ),
                    
                    ui.hr(style="margin: 0.5rem 0 1rem 0; border-color: #e2e8f0;"),
                    
                    ui.tags.label("Load Saved Scenario", style="font-weight: 500; margin-bottom: 0.25rem; display: block;"),
                    ui.input_select(
                        "selected_scenario",
                        None,
                        choices=[],
                        width="100%"
                    ),
                    
                    ui.hr(style="margin: 1rem 0; border-color: #e2e8f0;"),
                    
                    ui.div(
                        {"style": "margin-bottom: 0.5rem; font-weight: 500; color: #475569;"},
                        "Create New Scenario"
                    ),
                    ui.input_text(
                        "scenario_name",
                        None,
                        placeholder="Enter scenario name...",
                        width="100%"
                    ),
                    ui.div(
                        {"style": "display: flex; gap: 0.5rem; margin-top: 0.5rem;"},
                        ui.input_action_button(
                            "new_scenario",
                            "+ Create",
                            class_="btn btn-success",
                            style="flex: 1;"
                        ),
                        ui.input_action_button(
                            "delete_scenario",
                            "🗑️",
                            class_="btn btn-outline-danger",
                            title="Delete selected scenario"
                        )
                    )
                )
            )
        ),
        
        # Main Content Area
        ui.div(
            {"style": "flex: 1; min-width: 0;"},
            
            # Input Parameters Card
            ui.div(
                {"class": "card", "style": "margin-bottom: 1.5rem;"},
                ui.div(
                    {"class": "card-header"},
                    "Cost-effectiveness Model Outputs"
                ),
                # Shared 4-column grid so QALYs columns stay aligned across both drug sections
                ui.div(
                    {"class": "cost-grid"},

                    # ── New Drug section header ─────────────────────────────────────
                    ui.div(
                        {"style": "grid-column: 1 / -1; align-self: start; display: flex; align-items: center; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 2px solid #e2e8f0;"},
                        ui.div(
                            {"style": "width: 10px; height: 10px; border-radius: 50%; background: #2563eb; flex-shrink: 0;"}
                        ),
                        ui.output_ui("intervention_drug_header")
                    ),

                    # New Drug — col 1: Drug Acquisition Cost
                    ui.div(
                        {"class": "input-group", "style": "margin-bottom: 0;"},
                        ui.tags.label(ui.output_ui("intervention_cost_label")),
                        ui.input_numeric("c_drug_new", None, value=50000, min=0, step=1000)
                    ),

                    # New Drug — col 2: Pack Price
                    ui.div(
                        {"class": "input-group", "style": "margin-bottom: 0;"},
                        ui.tags.label(ui.output_ui("pack_price_label")),
                        ui.input_numeric("pack_price", None, value=2000, min=0, step=1000)
                    ),

                    # New Drug — col 3: Other Costs
                    ui.div(
                        {"class": "input-group", "style": "margin-bottom: 0;"},
                        ui.tags.label(ui.output_ui("intervention_other_costs_label")),
                        ui.input_numeric("c_other_new", None, value=150000, min=0, step=1000)
                    ),

                    # New Drug — col 4: Total QALYs
                    ui.div(
                        {"class": "input-group", "style": "margin-bottom: 0;"},
                        ui.tags.label("Total QALYs"),
                        ui.input_numeric("q_new", None, value=14.0, min=0, step=0.1)
                    ),

                    # ── Reference Drug section header ───────────────────────────────
                    ui.div(
                        {"style": "grid-column: 1 / -1; align-self: start; display: flex; align-items: center; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 2px solid #e2e8f0; margin-top: 0.5rem;"},
                        ui.div(
                            {"style": "width: 10px; height: 10px; border-radius: 50%; background: #8054E6; flex-shrink: 0;"}
                        ),
                        ui.output_ui("comparator_header")
                    ),

                    # Reference Drug — cols 1-3: Total Cost (spans to mirror the three new-drug cost fields)
                    ui.div(
                        {"class": "ref-cost-span"},
                        ui.div(
                            {"class": "input-group ref-cost-input", "style": "margin-bottom: 0;"},
                            ui.tags.label(ui.output_ui("comparator_cost_label")),
                            ui.input_numeric("c_total_ref", None, value=160000, min=0, step=1000)
                        )
                    ),

                    # Reference Drug — col 4: Total QALYs (aligned with New Drug's QALYs above)
                    ui.div(
                        {"class": "input-group", "style": "margin-bottom: 0;"},
                        ui.tags.label("Total QALYs"),
                        ui.input_numeric("q_ref", None, value=13.0, min=0, step=0.1)
                    ),
                ),
                
                # Calculate Button inside the card
                ui.div(
                    {"style": "text-align: center; padding: 1.25rem 1rem 1rem 1rem; border-top: 1px solid #e2e8f0; margin-top: 0.25rem;"},
                    ui.input_action_button(
                        "calculate_save",
                        "Calculate & Save",
                        class_="btn btn-primary btn-calculate"
                    )
                )
            ),

            ui.output_ui("validation_message"),

            # Hidden sentinel inputs — always in DOM so metrics_display can read them safely
            ui.div(
                {"style": "display: none;"},
                ui.input_numeric("icer_range_min", None, value=25000, min=0, step=1000),
                ui.input_numeric("icer_range_max", None, value=35000, min=0, step=1000)
            ),

            # Results Section (hidden until calculated)
            ui.output_ui("results_section")
        )
    )
)


# Server logic
def server(input, output, session):
    # Reactive values for storing scenarios
    scenarios = reactive.Value({})
    current_scenario_id = reactive.Value(None)
    show_results = reactive.Value(True)  # Show results by default
    
    # Reactive values for drug names and currency
    intervention_drug_name = reactive.Value("New Drug")
    comparator_name = reactive.Value("Reference Drug")
    selected_currency = reactive.Value("£")
    
    # Helper function to format currency values
    def format_currency(value, decimals=2):
        """Format a numeric value with the selected currency symbol."""
        if decimals == 0:
            return f"{selected_currency()}{value:,.0f}"
        else:
            return f"{selected_currency()}{value:,.{decimals}f}"

    @reactive.Effect
    @reactive.event(input.intervention_drug_name)
    def update_intervention_drug_name():
        """Update intervention drug name."""
        name = input.intervention_drug_name()
        if name and name.strip():
            intervention_drug_name.set(name)

    @reactive.Effect
    @reactive.event(input.comparator_name)
    def update_comparator_name():
        """Update comparator name."""
        name = input.comparator_name()
        if name and name.strip():
            comparator_name.set(name)

    @reactive.Effect
    @reactive.event(input.currency_select)
    def update_currency():
        """Update selected currency."""
        currency = input.currency_select()
        if currency:
            selected_currency.set(currency)

    @reactive.Effect
    @reactive.event(input.corridor_min_thr)
    def sync_corridor_min():
        """Sync editable corridor min input → hidden sentinel so calculations update."""
        try:
            val = input.corridor_min_thr()
            if val is not None:
                ui.update_numeric("icer_range_min", value=val)
        except Exception:
            pass

    @reactive.Effect
    @reactive.event(input.corridor_max_thr)
    def sync_corridor_max():
        """Sync editable corridor max input → hidden sentinel so calculations update."""
        try:
            val = input.corridor_max_thr()
            if val is not None:
                ui.update_numeric("icer_range_max", value=val)
        except Exception:
            pass

    @reactive.Effect
    @reactive.event(input.new_scenario)
    def create_new_scenario():
        """Create a new empty scenario."""
        name = input.scenario_name()

        if not name or name.strip() == "":
            ui.notification_show(
                "Please enter a scenario name",
                type="warning",
                duration=3
            )
            return

        # Check for duplicate names
        current_scenarios = scenarios()
        if name in current_scenarios:
            ui.notification_show(
                f"Scenario '{name}' already exists. Choose a different name.",
                type="warning",
                duration=3
            )
            return

        # Create new scenario with current input values
        new_scenario = ICERScenario(
            name=name,
            description="",
            c_drug_new=input.c_drug_new(),
            c_other_new=input.c_other_new(),
            q_new=input.q_new(),
            c_total_ref=input.c_total_ref(),
            q_ref=input.q_ref(),
            icer_threshold=50000,
            pack_price=input.pack_price() or 0,
            icer_range_min=input.icer_range_min() or 25000,
            icer_range_max=input.icer_range_max() or 35000,
        )

        # Add to scenarios
        updated_scenarios = current_scenarios.copy()
        updated_scenarios[name] = new_scenario
        scenarios.set(updated_scenarios)
        current_scenario_id.set(name)

        ui.notification_show(
            f"✅ Scenario '{name}' created. Adjust parameters and click 'Calculate & Save' to update it.",
            type="message",
            duration=4
        )
        
        # Clear the name input
        ui.update_text("scenario_name", value="")

    @reactive.Effect
    @reactive.event(input.calculate_save)
    def calculate_and_save():
        """Calculate results and optionally save to current scenario."""
        current_id = current_scenario_id()

        is_valid, error_msg = validate_inputs(
            input.c_drug_new(),
            input.c_other_new(),
            input.c_total_ref(),
            input.q_new(),
            input.q_ref(),
            input.icer_range_min() or 25000
        )

        if not is_valid:
            ui.notification_show(
                f"Invalid inputs: {error_msg}",
                type="error",
                duration=5
            )
            return

        # If we have a current scenario, update it with current values
        if current_id:
            current_scenarios = scenarios()
            updated_scenario = ICERScenario(
                name=current_id,
                description="",
                c_drug_new=input.c_drug_new(),
                c_other_new=input.c_other_new(),
                q_new=input.q_new(),
                c_total_ref=input.c_total_ref(),
                q_ref=input.q_ref(),
                icer_threshold=50000,
                pack_price=input.pack_price() or 0,
                icer_range_min=input.icer_range_min() or 25000,
                icer_range_max=input.icer_range_max() or 35000,
            )

            updated_scenarios = current_scenarios.copy()
            updated_scenarios[current_id] = updated_scenario
            scenarios.set(updated_scenarios)
            
            ui.notification_show(
                f"✅ Results calculated and saved to '{current_id}'",
                type="message",
                duration=3
            )
        else:
            # No scenario selected - create a "Base Case" scenario automatically
            base_case_name = "Base Case"
            current_scenarios = scenarios()
            
            # If Base Case already exists, use a numbered variant
            counter = 1
            original_name = base_case_name
            while base_case_name in current_scenarios:
                base_case_name = f"{original_name} {counter}"
                counter += 1
            
            # Create the Base Case scenario
            base_scenario = ICERScenario(
                name=base_case_name,
                description="Automatically created base case scenario",
                c_drug_new=input.c_drug_new(),
                c_other_new=input.c_other_new(),
                q_new=input.q_new(),
                c_total_ref=input.c_total_ref(),
                q_ref=input.q_ref(),
                icer_threshold=50000,
                pack_price=input.pack_price() or 0,
                icer_range_min=input.icer_range_min() or 25000,
                icer_range_max=input.icer_range_max() or 35000,
            )

            # Add to scenarios and set as current
            updated_scenarios = current_scenarios.copy()
            updated_scenarios[base_case_name] = base_scenario
            scenarios.set(updated_scenarios)
            current_scenario_id.set(base_case_name)
            
            ui.notification_show(
                f"✅ Results calculated and saved to '{base_case_name}'",
                type="message",
                duration=3
            )
        
        # Show results regardless of whether we saved
        show_results.set(True)

    @reactive.Effect
    @reactive.event(input.delete_scenario)
    def delete_scenario():
        """Delete the currently selected scenario."""
        current_id = current_scenario_id()

        if not current_id:
            ui.notification_show(
                "No scenario selected",
                type="warning",
                duration=3
            )
            return

        current_scenarios = scenarios()
        if current_id in current_scenarios:
            updated_scenarios = current_scenarios.copy()
            del updated_scenarios[current_id]
            scenarios.set(updated_scenarios)

            # Reset selection
            if updated_scenarios:
                current_scenario_id.set(list(updated_scenarios.keys())[0])
                show_results.set(True)  # Show results for the next scenario
            else:
                current_scenario_id.set(None)
                show_results.set(False)  # Hide results when no scenarios

            ui.notification_show(
                f"🗑️ Scenario '{current_id}' deleted",
                type="message",
                duration=3
            )

    @output
    @render.ui
    def intervention_drug_header():
        """Render intervention drug header with dynamic name."""
        return ui.span(
            intervention_drug_name(),
            style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0;"
        )
    
    @output
    @render.ui
    def comparator_header():
        """Render comparator header with dynamic name."""
        return ui.span(
            comparator_name(),
            style="font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0;"
        )
    
    @output
    @render.ui
    def intervention_cost_label():
        """Render intervention drug cost label with dynamic currency."""
        return f"Total Drug Cost (lifetime, {selected_currency()}/QALY)"
    
    @output
    @render.ui
    def pack_price_label():
        """Render pack price label with dynamic currency."""
        return f"Pack Price ({selected_currency()})"
    
    @output
    @render.ui
    def intervention_other_costs_label():
        """Render intervention other costs label with dynamic currency."""
        return f"Total Other Costs (lifetime, {selected_currency()})"
    
    @output
    @render.ui
    def comparator_cost_label():
        """Render comparator cost label with dynamic currency."""
        return f"Total Cost (lifetime, {selected_currency()})"
    
    @output
    @render.ui
    def min_threshold_label():
        """Render min threshold label with dynamic currency."""
        return f"Min Threshold ({selected_currency()}/QALY)"
    
    @output
    @render.ui
    def max_threshold_label():
        """Render max threshold label with dynamic currency."""
        return f"Max Threshold ({selected_currency()}/QALY)"

    @output
    @render.ui
    def display_min_threshold_section():
        """Editable min threshold inside the Price Corridor."""
        return ui.div(
            {"class": "input-group", "style": "margin-bottom: 0;"},
            ui.tags.label(ui.output_ui("min_threshold_label")),
            ui.input_numeric(
                "corridor_min_thr",
                None,
                value=input.icer_range_min() or 25000,
                min=0,
                step=1000,
                width="100%"
            )
        )

    @output
    @render.ui
    def display_max_threshold_section():
        """Editable max threshold inside the Price Corridor."""
        return ui.div(
            {"class": "input-group", "style": "margin-bottom: 0;"},
            ui.tags.label(ui.output_ui("max_threshold_label")),
            ui.input_numeric(
                "corridor_max_thr",
                None,
                value=input.icer_range_max() or 35000,
                min=0,
                step=1000,
                width="100%"
            )
        )

    @reactive.Effect
    def sync_scenario_selector():
        """Keep the scenario dropdown choices in sync without replacing the DOM element.
        Using ui.update_select avoids spurious input.selected_scenario events that would
        overwrite UI inputs whenever any scenario is saved."""
        current_scenarios = scenarios()
        scenario_names = list(current_scenarios.keys())
        selected = current_scenario_id() or (scenario_names[0] if scenario_names else None)
        ui.update_select("selected_scenario", choices=scenario_names, selected=selected)

    @reactive.Effect
    @reactive.event(input.selected_scenario)
    def update_current_scenario():
        """Update current scenario when selection changes.
        Only reloads UI inputs when the user switches to a DIFFERENT scenario than the
        currently tracked one. This prevents sync_scenario_selector's programmatic
        ui.update_select calls from overwriting inputs the user just entered."""
        new_id = input.selected_scenario()
        if not new_id:
            return

        # Always keep current_scenario_id in sync with the dropdown
        prev_id = current_scenario_id()
        current_scenario_id.set(new_id)

        # Only reload input fields when the user genuinely switches to a different scenario
        if new_id == prev_id:
            return

        current_scenarios = scenarios()
        if new_id in current_scenarios:
            scenario = current_scenarios[new_id]
            ui.update_numeric("c_drug_new", value=scenario.c_drug_new)
            ui.update_numeric("c_other_new", value=scenario.c_other_new)
            ui.update_numeric("q_new", value=scenario.q_new)
            ui.update_numeric("c_total_ref", value=scenario.c_total_ref)
            ui.update_numeric("q_ref", value=scenario.q_ref)
            if scenario.pack_price > 0:
                ui.update_numeric("pack_price", value=scenario.pack_price)
            if scenario.icer_range_min > 0:
                ui.update_numeric("icer_range_min", value=scenario.icer_range_min)
            if scenario.icer_range_max > 0:
                ui.update_numeric("icer_range_max", value=scenario.icer_range_max)
            show_results.set(True)

    @output
    @render.ui
    def validation_message():
        """Display validation errors if any."""
        is_valid, error_msg = validate_inputs(
            input.c_drug_new(),
            input.c_other_new(),
            input.c_total_ref(),
            input.q_new(),
            input.q_ref(),
            input.icer_range_min() or 25000
        )

        if not is_valid:
            return ui.div(
                {"class": "alert alert-danger"},
                ui.tags.strong("⚠️ Invalid Input: "),
                error_msg
            )

        return None

    @output
    @render.ui
    def results_section():
        """Wrapper for all results - shown after Calculate & Save."""
        if not show_results():
            return ui.div(
                {"class": "card", "style": "text-align: center; padding: 3rem; color: #64748b;"},
                ui.div(
                    ui.tags.i(class_="fas fa-calculator", style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"),
                    ui.h4("Results will appear here", style="margin: 1rem 0 0.5rem 0; color: #94a3b8;"),
                    ui.p("Enter parameters and click 'Calculate & Save' to see results", style="margin: 0;")
                )
            )
        
        # Show all results
        return ui.div(
            # Key Metrics
            ui.output_ui("metrics_display"),

            # Scenario Comparison
            ui.output_ui("comparison_view"),

            # ICER Discount Curve Visualization (inlined — avoids first-render race condition)
            _icer_plot_card(),

            # Export
            ui.div(
                {"class": "card"},
                ui.div(
                    {"class": "card-header"},
                    "📥 Export Results"
                ),
                ui.download_button(
                    "download_report",
                    "📄 Download Report (HTML)",
                    class_="btn btn-primary"
                )
            )
        )

    @output
    @render.ui
    def metrics_display():
        """Display key metrics."""
        is_valid, _ = validate_inputs(
            input.c_drug_new(),
            input.c_other_new(),
            input.c_total_ref(),
            input.q_new(),
            input.q_ref(),
            input.icer_range_min() or 25000
        )

        if not is_valid:
            return None

        # Get discount range to use for metrics
        min_thr = input.icer_range_min() or 25000
        max_thr = input.icer_range_max() or 35000
        if min_thr > max_thr:
            min_thr, max_thr = max_thr, min_thr
        avg_thr = (min_thr + max_thr) / 2  # Use average for single metrics display

        # Create temporary scenario for calculation using average threshold
        temp_scenario = ICERScenario(
            name="Current",
            c_drug_new=input.c_drug_new(),
            c_other_new=input.c_other_new(),
            q_new=input.q_new(),
            c_total_ref=input.c_total_ref(),
            q_ref=input.q_ref(),
            icer_threshold=avg_thr
        )

        results = calculate_scenario_results(temp_scenario)

        if not results['valid']:
            return None

        # Compute range values at both ends of the ICER threshold range
        def justified_for_threshold(thr):
            threshold_scenario = ICERScenario(
                name="Current",
                c_drug_new=input.c_drug_new(),
                c_other_new=input.c_other_new(),
                q_new=input.q_new(),
                c_total_ref=input.c_total_ref(),
                q_ref=input.q_ref(),
                icer_threshold=thr
            )
            threshold_results = calculate_scenario_results(threshold_scenario)
            if not threshold_results['valid']:
                return 0.0
            return threshold_results['justified_price']

        justified_min = justified_for_threshold(min_thr)
        justified_max = justified_for_threshold(max_thr)

        # Match scenario comparison table logic: apply discount range to pack price
        pack_price = input.pack_price() or 50000
        current_drug_cost = input.c_drug_new() or 0
        if current_drug_cost > 0:
            min_pct_for_price = max((current_drug_cost - justified_min) / current_drug_cost * 100, 0.0)
            max_pct_for_price = max((current_drug_cost - justified_max) / current_drug_cost * 100, 0.0)
        else:
            min_pct_for_price = 0.0
            max_pct_for_price = 0.0

        min_adj_price = pack_price * (1 -min_pct_for_price / 100)
        max_adj_price = pack_price * (1 - max_pct_for_price / 100)
        if min_adj_price == max_adj_price:
            justified_range_display = format_currency(min_adj_price, decimals=2)
        else:
            justified_range_display = f"{format_currency(min_adj_price, decimals=2)} – {format_currency(max_adj_price, decimals=2)}"

        # Calculate discount/increase scenarios
        drug_cost = results['c_drug_new']
        justified_price = results['justified_price']
        
        # Scenario 1: Discount needed (if current price is above justified price)
        if justified_price < drug_cost and drug_cost > 0:
            discount_pct = (drug_cost - justified_price) / drug_cost * 100
            discount_value = drug_cost - justified_price
            need_discount = True
        else:
            discount_pct = 0.0
            discount_value = 0.0
            need_discount = False

        # Discount range display across threshold range
        if drug_cost > 0:
            discount_min = max((drug_cost - justified_min) / drug_cost * 100, 0.0)
            discount_max = max((drug_cost - justified_max) / drug_cost * 100, 0.0)
        else:
            discount_min = 0.0
            discount_max = 0.0

        if discount_min == discount_max:
            discount_range_display = f"{discount_min:.1f}%"
        else:
            discount_range_display = f"{discount_min:.1f}% – {discount_max:.1f}%"

        # Scenario 2: Price increase possible (if current price is below justified price)
        if justified_price > drug_cost and drug_cost > 0:
            increase_value = justified_price - drug_cost
            increase_pct = (increase_value / drug_cost) * 100
            can_increase = True
        else:
            increase_value = 0.0
            increase_pct = 0.0
            can_increase = False
        can_increase = False  # TEMP: disabled to demonstrate discount/increase scenarios

        # Build metric cards based on scenarios
        metric_cards = []

        # Always show justified price
        metric_cards.append(
            ui.div(
                {"class": "metric-card"},
                ui.div("Justified Pack Price", class_="metric-label"),
                ui.div(justified_range_display, class_="metric-value"))
        )

        # Show per-threshold discount cards
        # Lower threshold card
        if discount_min > 0:
            min_adj_pack = pack_price * (1 - discount_min / 100)
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div(f"Discount at £{min_thr:,.0f} Threshold", class_="metric-label"),
                    ui.div(f"{discount_min:.1f}%", class_="metric-value", style="color: #ef4444;"),
                    ui.div(f"Adjusted pack price: {format_currency(min_adj_pack, decimals=2)}", class_="help-text")
                )
            )
        else:
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div(f"Discount at £{min_thr:,.0f} Threshold", class_="metric-label"),
                    ui.div("0%", class_="metric-value", style="color: #10b981;"),
                    ui.div(f"No discount needed at £{min_thr:,.0f} threshold", class_="help-text")
                )
            )

        # Higher threshold card
        if discount_max > 0:
            max_adj_pack = pack_price * (1 - discount_max / 100)
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div(f"Discount at £{max_thr:,.0f} Threshold", class_="metric-label"),
                    ui.div(f"{discount_max:.1f}%", class_="metric-value", style="color: #ef4444;"),
                    ui.div(f"Adjusted pack price: {format_currency(max_adj_pack, decimals=2)}", class_="help-text")
                )
            )
        else:
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div(f"Discount at £{max_thr:,.0f} Threshold", class_="metric-label"),
                    ui.div("0%", class_="metric-value", style="color: #10b981;"),
                    ui.div(f"No discount needed at £{max_thr:,.0f} threshold", class_="help-text")
                )
            )

        # Show increase scenario if applicable
        if can_increase:
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div("% Price Increase Possible", class_="metric-label"),
                    ui.div(f"{increase_pct:.1f}%", class_="metric-value", style="color: #10b981;"),
                    ui.div(f"Price can increase by: {format_currency(increase_value, decimals=2)}", class_="help-text")
                )
            )
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div("Value of Possible Increase", class_="metric-label"),
                    ui.div(format_currency(increase_value, decimals=2), class_="metric-value", style="color: #10b981;"),
                    ui.div(f"Current: {format_currency(drug_cost, decimals=0)} → Max: {format_currency(justified_price, decimals=0)}", class_="help-text")
                )
            )

        # If neither discount nor increase, drug is perfectly priced
        if not need_discount and not can_increase:
            metric_cards.append(
                ui.div(
                    {"class": "metric-card"},
                    ui.div("Status", class_="metric-label"),
                    ui.div("✓ Perfectly Priced", class_="metric-value", style="color: #10b981;"),
                    ui.div(f"Drug price is at the justified price point", class_="help-text")
                )
            )

        return ui.div(
            {"class": "card"},
            ui.div(
                {"class": "card-header"},
                "📊 Price Corridor"
            ),
            
            # Discount Analysis Range Section (inside Price Corridor)
            ui.div(
                {"style": "padding: 1.5rem; border-bottom: 1px solid #e2e8f0;"},
                ui.div(
                    {"style": "margin-bottom: 1rem;"},
                    ui.h4("Discount Analysis Range", style="margin: 0 0 1rem 0; color: #1e293b;")
                ),
                ui.div(
                    {"style": "display: flex; gap: 1.5rem; flex-wrap: wrap;"},
                    ui.div(
                        {"style": "flex: 1; min-width: 200px;"},
                        ui.output_ui("display_min_threshold_section")
                    ),
                    ui.div(
                        {"style": "flex: 1; min-width: 200px;"},
                        ui.output_ui("display_max_threshold_section")
                    )
                ),
                ui.div("Discount range calculated between these thresholds", class_="help-text", style="margin-top: 0.5rem;")
            ),

            # Metric Cards Grid
            ui.div(
                {"class": "metric-grid"},
                *metric_cards
            )
        )

    def _icer_plot_card():
        """Build the ICER plot card inline.
        Called directly from results_section so scenarios() is read inside the
        same reactive render context — no separate output, no race condition."""
        current_scenarios = scenarios()

        if len(current_scenarios) > 1:
            scenario_list = list(current_scenarios.values())
            fig = create_icer_discount_plot(scenario_list)
        else:
            # If no scenarios yet, use input values directly (first render fix)
            if not current_scenarios:
                min_thr = input.icer_range_min() or 25000
                max_thr = input.icer_range_max() or 35000
                avg_thr = (min_thr + max_thr) / 2
                temp_scenario = ICERScenario(
                    name="Current",
                    c_drug_new=input.c_drug_new(),
                    c_other_new=input.c_other_new(),
                    q_new=input.q_new(),
                    c_total_ref=input.c_total_ref(),
                    q_ref=input.q_ref(),
                    icer_threshold=avg_thr
                )
            else:
                sc = list(current_scenarios.values())[0]
                avg_thr = (sc.icer_range_min + sc.icer_range_max) / 2
                temp_scenario = ICERScenario(
                    name=sc.name,
                    c_drug_new=sc.c_drug_new,
                    c_other_new=sc.c_other_new,
                    q_new=sc.q_new,
                    c_total_ref=sc.c_total_ref,
                    q_ref=sc.q_ref,
                    icer_threshold=avg_thr
                )
            
            results = calculate_scenario_results(temp_scenario)

            if not results['valid']:
                return None

            fig = create_icer_discount_plot(temp_scenario, results)

        fig.update_xaxes(title_text=f"ICER ({selected_currency()}/QALY)", tickformat=",d")
        fig.update_yaxes(
            title_text="Price Discount (%)",
            tickmode="array",
            tickvals=list(range(0, 101, 10)),
            tickformat=".1f",
            range=[0, 100]
        )
        fig.update_layout(
            title=None,
            xaxis=dict(zeroline=True, rangemode='tozero', anchor='y'),
            yaxis=dict(zeroline=True, rangemode='tozero', anchor='x')
        )

        plot_html = fig.to_html(
            include_plotlyjs='cdn',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'responsive': True,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
            }
        )

        return ui.div(
            {"class": "card"},
            ui.div({"class": "card-header"}, "📈 Price Discount vs ICER"),
            ui.HTML(plot_html)
        )



    @output
    @render.ui
    def comparison_view():
        """Display scenario comparison."""
        current_scenarios = scenarios()

        if len(current_scenarios) < 1:
            return None

        # Calculate results for all scenarios
        scenario_list = list(current_scenarios.values())
        comparison = compare_scenarios(scenario_list)

        if 'error' in comparison:
            return None

        # Create comparison table
        rows = []

        for scenario in scenario_list:
            # Use each scenario's own saved values — not the global UI inputs
            s_pack_price = scenario.pack_price if scenario.pack_price > 0 else (input.pack_price() or 2000)
            s_min_thr = scenario.icer_range_min if scenario.icer_range_min > 0 else (input.icer_range_min() or 25000)
            s_max_thr = scenario.icer_range_max if scenario.icer_range_max > 0 else (input.icer_range_max() or 35000)
            if s_min_thr > s_max_thr:
                s_min_thr, s_max_thr = s_max_thr, s_min_thr

            if s_min_thr == s_max_thr:
                thr_label = format_currency(s_min_thr, decimals=0)
            else:
                thr_label = f"{format_currency(s_min_thr, decimals=0)} – {format_currency(s_max_thr, decimals=0)}"

            drug_cost = scenario.c_drug_new

            # compute discount percentage at each end of this scenario's threshold range
            def pct_for_threshold(thr, sc=scenario, dc=drug_cost):
                temp = ICERScenario(
                    name=sc.name,
                    description=sc.description,
                    c_drug_new=sc.c_drug_new,
                    c_other_new=sc.c_other_new,
                    q_new=sc.q_new,
                    c_total_ref=sc.c_total_ref,
                    q_ref=sc.q_ref,
                    icer_threshold=thr
                )
                res = calculate_scenario_results(temp)
                if not res['valid'] or dc <= 0:
                    return 0.0
                justified = res['justified_price']
                if justified < dc:
                    return (dc - justified) / dc * 100
                return 0.0

            min_pct = pct_for_threshold(s_min_thr)
            max_pct = pct_for_threshold(s_max_thr)

            # apply discount to this scenario's pack price
            min_adj_price = s_pack_price * (1 - min_pct / 100)
            max_adj_price = s_pack_price * (1 - max_pct / 100)
            if min_adj_price == max_adj_price:
                justifiable_display = format_currency(min_adj_price, decimals=2)
            else:
                justifiable_display = f"{format_currency(min_adj_price, decimals=2)} – {format_currency(max_adj_price, decimals=2)}"

            if min_pct == max_pct:
                range_str = f"{min_pct:.2f}%"
            else:
                range_str = f"{min_pct:.2f}% – {max_pct:.2f}%"

            rows.append(
                ui.tags.tr(
                    ui.tags.td(scenario.name),
                    ui.tags.td(thr_label),
                    ui.tags.td(format_currency(s_pack_price, decimals=2)),
                    ui.tags.td(justifiable_display),
                    ui.tags.td(range_str)
                )
            )

        return ui.div(
            {"class": "card"},
            ui.div(
                {"class": "card-header"},
                f"📊 Scenario Comparison ({comparison['num_scenarios']} scenario[s])"
            ),

            ui.div(
                {"class": "table-scroll"},
                ui.tags.table(
                    {"class": "comparison-table"},
                    ui.tags.thead(
                        ui.tags.tr(
                            ui.tags.th("Scenario"),
                            ui.tags.th("ICER Threshold Range"),
                            ui.tags.th("Pack Price"),
                            ui.tags.th("Justifiable Pack Price"),
                            ui.tags.th("% Discount Range")
                        )
                    ),
                    ui.tags.tbody(*rows)
                )
            ),

        )

    @render.download(filename=lambda: f"PriceLens_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    def download_report():
        """Generate and download a full HTML report with inputs, comparison table and interactive plot."""
        current_scenarios = scenarios()
        currency = selected_currency()

        def fmt(value, decimals=2):
            if decimals == 0:
                return f"{currency}{value:,.0f}"
            return f"{currency}{value:,.{decimals}f}"

        if not current_scenarios:
            yield "<html><body><p>No scenarios to report.</p></body></html>"
            return

        intervention = intervention_drug_name()
        comparator   = comparator_name()

        # ── Scenario inputs section ──────────────────────────────────────────
        inputs_html = ""
        comparison_rows_html = ""

        for scenario in current_scenarios.values():
            # Inputs card
            inputs_html += f"""
            <div class="scenario-card">
                <h3>{scenario.name}</h3>
                <table class="data-table">
                    <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
                    <tbody>
                        <tr><td>Drug Acquisition Cost (per course) – {intervention}</td><td>{fmt(scenario.c_drug_new)}</td></tr>
                        <tr><td>Other Treatment Costs – {intervention}</td><td>{fmt(scenario.c_other_new)}</td></tr>
                        <tr><td>Total Treatment Cost – {intervention}</td><td>{fmt(scenario.c_drug_new + scenario.c_other_new)}</td></tr>
                        <tr><td>QALYs Gained – {intervention}</td><td>{scenario.q_new:.4f}</td></tr>
                        <tr><td>Total Cost – {comparator}</td><td>{fmt(scenario.c_total_ref)}</td></tr>
                        <tr><td>QALYs Gained – {comparator}</td><td>{scenario.q_ref:.4f}</td></tr>
                        <tr><td>Pack Price – {intervention}</td><td>{fmt(scenario.pack_price)}</td></tr>
                        <tr><td>ICER Threshold Range</td><td>{fmt(scenario.icer_range_min, 0)} – {fmt(scenario.icer_range_max, 0)}/QALY</td></tr>
                    </tbody>
                </table>
            </div>
            """

            # ── Comparison table row (mirrors comparison_view logic) ──────────
            s_pack_price = scenario.pack_price if scenario.pack_price > 0 else 2000
            s_min_thr = scenario.icer_range_min if scenario.icer_range_min > 0 else 25000
            s_max_thr = scenario.icer_range_max if scenario.icer_range_max > 0 else 35000
            if s_min_thr > s_max_thr:
                s_min_thr, s_max_thr = s_max_thr, s_min_thr

            thr_label = (fmt(s_min_thr, 0) if s_min_thr == s_max_thr
                         else f"{fmt(s_min_thr, 0)} – {fmt(s_max_thr, 0)}")

            drug_cost = scenario.c_drug_new

            def pct_for_threshold(thr, sc=scenario, dc=drug_cost):
                temp = ICERScenario(
                    name=sc.name, description=sc.description,
                    c_drug_new=sc.c_drug_new, c_other_new=sc.c_other_new,
                    q_new=sc.q_new, c_total_ref=sc.c_total_ref,
                    q_ref=sc.q_ref, icer_threshold=thr
                )
                res = calculate_scenario_results(temp)
                if not res['valid'] or dc <= 0:
                    return 0.0
                justified = res['justified_price']
                return (dc - justified) / dc * 100 if justified < dc else 0.0

            min_pct = pct_for_threshold(s_min_thr)
            max_pct = pct_for_threshold(s_max_thr)

            min_adj = s_pack_price * (1 - min_pct / 100)
            max_adj = s_pack_price * (1 - max_pct / 100)
            justifiable_display = (fmt(min_adj) if min_adj == max_adj
                                   else f"{fmt(min_adj)} – {fmt(max_adj)}")
            range_str = (f"{min_pct:.2f}%" if min_pct == max_pct
                         else f"{min_pct:.2f}% – {max_pct:.2f}%")

            comparison_rows_html += f"""
                <tr>
                    <td>{scenario.name}</td>
                    <td>{thr_label}</td>
                    <td>{fmt(s_pack_price)}</td>
                    <td>{justifiable_display}</td>
                    <td>{range_str}</td>
                </tr>"""

        # ── Build the Plotly figure ───────────────────────────────────────────
        scenario_list = list(current_scenarios.values())
        if len(scenario_list) > 1:
            fig = create_icer_discount_plot(scenario_list)
        else:
            sc0 = scenario_list[0]
            avg_thr = (sc0.icer_range_min + sc0.icer_range_max) / 2
            temp_sc = ICERScenario(
                name=sc0.name, c_drug_new=sc0.c_drug_new,
                c_other_new=sc0.c_other_new, q_new=sc0.q_new,
                c_total_ref=sc0.c_total_ref, q_ref=sc0.q_ref,
                icer_threshold=avg_thr
            )
            fig = create_icer_discount_plot(temp_sc, calculate_scenario_results(temp_sc))

        fig.update_xaxes(title_text=f"ICER ({currency}/QALY)", tickformat=",d")
        fig.update_yaxes(
            title_text="Price Discount (%)",
            tickmode="array",
            tickvals=list(range(0, 101, 10)),
            tickformat=".1f",
            range=[0, 100]
        )
        fig.update_layout(title=None)
        plot_div = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={"displayModeBar": True, "displaylogo": False,
                    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]}
        )

        num_scenarios = len(current_scenarios)
        report_date = datetime.now().strftime("%d %B %Y, %H:%M")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PriceLens by Symmetron Analysis Report – {report_date}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1100px; margin: 40px auto; padding: 0 24px;
            color: #1e293b; background: #f8fafc; }}
    h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 12px; margin-bottom: 4px; }}
    h2 {{ color: #334155; margin-top: 40px; padding-left: 12px;
          border-left: 4px solid #2563eb; }}
    h3 {{ color: #2563eb; margin: 0 0 12px; }}
    .meta {{ color: #64748b; margin-bottom: 32px; font-size: 0.9rem; }}
    .scenario-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
                      padding: 20px 24px; margin-bottom: 20px;
                      box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
    .data-table, .comparison-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    .data-table th, .comparison-table th {{ background: #2563eb; color: #fff;
                                             padding: 10px 14px; text-align: left;
                                             font-size: 0.85rem; }}
    .data-table td, .comparison-table td {{ padding: 9px 14px;
                                             border-bottom: 1px solid #e2e8f0;
                                             font-size: 0.9rem; }}
    .data-table tr:last-child td, .comparison-table tr:last-child td {{ border-bottom: none; }}
    .data-table tr:nth-child(even) td {{ background: #f8fafc; }}
    .comparison-table tr:hover td {{ background: #eff6ff; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
             padding: 20px 24px; margin-top: 16px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
    .footer {{ text-align: center; margin-top: 56px; padding: 20px 16px;
               border-top: 1px solid #e2e8f0; }}
    .footer-brand {{ display: inline-flex; align-items: center; gap: 8px;
                     color: #2563eb; font-size: 0.95rem; font-weight: 600;
                     letter-spacing: 0.01em; }}
    .footer-brand span.at {{ color: #64748b; font-weight: 400; }}
    .footer-brand span.sym {{ color: #1e293b; font-weight: 700; }}
    .footer-sub {{ color: #94a3b8; font-size: 0.75rem; margin-top: 4px; }}
  </style>
</head>
<body>
  <h1>&#128138; PriceLens by Symmetron – Analysis Report</h1>
  <p class="meta">Generated: {report_date} &nbsp;|&nbsp; {num_scenarios} scenario{"s" if num_scenarios != 1 else ""}</p>

  <h2>Scenario Inputs</h2>
  {inputs_html}

  <h2>Scenario Comparison</h2>
  <div class="card">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Scenario</th>
          <th>ICER Threshold Range</th>
          <th>Pack Price</th>
          <th>Justifiable Pack Price</th>
          <th>% Discount Range</th>
        </tr>
      </thead>
      <tbody>
        {comparison_rows_html}
      </tbody>
    </table>
  </div>

  <h2>Price Discount vs ICER Chart</h2>
  <div class="card">
    {plot_div}
  </div>

  <div class="footer">
    <div class="footer-brand">
      &#128138; PriceLens <span class="at">&nbsp;@&nbsp;</span><span class="sym">Symmetron Limited</span>
    </div>
    <div class="footer-sub">Confidential &nbsp;·&nbsp; Generated {report_date}</div>
  </div>
</body>
</html>"""

        yield html


# Create app with static files directory
# Get the directory where app.py is located for static files
app_dir = Path(__file__).parent

app = App(app_ui, server, static_assets=app_dir)

# Run the app when this script is executed directly
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001)

