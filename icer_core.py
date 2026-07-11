"""
ICER Core Calculator Module
Provides pure, reactive functions for ICER calculations and cost-effectiveness analysis.
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import plotly.graph_objects as go


@dataclass
class ICERScenario:
    """Data class for storing a single ICER scenario."""
    name: str
    description: str = ""

    # New drug parameters
    c_drug_new: float = 0.0
    c_other_new: float = 0.0
    q_new: float = 0.0

    # Reference drug parameters
    c_total_ref: float = 0.0
    q_ref: float = 0.0

    # ICER threshold (used for single-point calculations)
    icer_threshold: float = 50000.0

    # Price corridor / threshold range and pack price (per-scenario)
    pack_price: float = 0.0
    icer_range_min: float = 25000.0
    icer_range_max: float = 35000.0

    # Metadata
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        """Convert scenario to dictionary."""
        return asdict(self)


def calculate_derived_values(scenario: ICERScenario) -> Dict[str, float]:
    """
    Calculate derived values from scenario inputs.

    Returns:
        Dictionary with c_total_new, delta_q, delta_c
    """
    c_total_new = scenario.c_drug_new + scenario.c_other_new
    delta_q = scenario.q_new - scenario.q_ref
    delta_c = c_total_new - scenario.c_total_ref

    return {
        'c_total_new': c_total_new,
        'delta_q': delta_q,
        'delta_c': delta_c
    }


def calculate_icer(c_drug_new: float, c_other_new: float, c_total_ref: float,
                   q_new: float, q_ref: float, discount_rate: float = 0.0) -> float:
    """
    Calculate ICER for given parameters.

    Formula: ICER = (C_Drug_new*(1-D) + C_Other_new - C_Total_ref) / DeltaQ

    Args:
        c_drug_new: Drug acquisition cost for new intervention
        c_other_new: Other costs for new intervention
        c_total_ref: Total costs for reference intervention
        q_new: QALYs for new intervention
        q_ref: QALYs for reference intervention
        discount_rate: Discount rate (0 to 1)

    Returns:
        ICER value (cost per QALY gained)
    """
    delta_q = q_new - q_ref

    if delta_q == 0:
        raise ValueError("DeltaQ cannot be zero (Q_new must differ from Q_ref)")

    numerator = c_drug_new * (1 - discount_rate) + c_other_new - c_total_ref
    icer = numerator / delta_q

    return icer


def calculate_justified_price(c_other_new: float, c_total_ref: float,
                              q_new: float, q_ref: float,
                              icer_threshold: float) -> float:
    """
    Calculate the justified drug price based on ICER threshold.

    Rearranging ICER formula:
    C_Drug_new = ICER * DeltaQ - C_Other_new + C_Total_ref

    Args:
        c_other_new: Other costs for new intervention
        c_total_ref: Total costs for reference intervention
        q_new: QALYs for new intervention
        q_ref: QALYs for reference intervention
        icer_threshold: Maximum acceptable ICER (willingness-to-pay per QALY)

    Returns:
        Justified drug price (maximum drug cost to meet threshold)
    """
    delta_q = q_new - q_ref

    if delta_q == 0:
        raise ValueError("DeltaQ cannot be zero (Q_new must differ from Q_ref)")

    # Rearrange ICER formula to solve for C_Drug_new
    justified_price = icer_threshold * delta_q - c_other_new + c_total_ref

    return justified_price


def is_cost_effective(icer: float, threshold: float) -> bool:
    """
    Determine if an intervention is cost-effective.

    Args:
        icer: Calculated ICER value
        threshold: Maximum acceptable ICER threshold

    Returns:
        True if ICER <= threshold (cost-effective), False otherwise
    """
    return icer <= threshold


def calculate_icer_elasticity(c_drug_new: float, delta_q: float) -> float:
    """
    Calculate ICER elasticity (sensitivity to discount rate changes).

    Formula: dICER/dD = -C_Drug_new / DeltaQ

    Args:
        c_drug_new: Drug acquisition cost
        delta_q: Incremental QALYs

    Returns:
        Elasticity coefficient (change in ICER per unit change in discount)
    """
    if delta_q == 0:
        raise ValueError("DeltaQ cannot be zero")

    return -c_drug_new / delta_q


def generate_icer_curve(c_drug_new: float, c_other_new: float, c_total_ref: float,
                       q_new: float, q_ref: float,
                       num_points: int = 201) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate ICER curve across discount rates from 0% to 100%.

    Args:
        c_drug_new: Drug acquisition cost
        c_other_new: Other costs
        c_total_ref: Reference total costs
        q_new: New drug QALYs
        q_ref: Reference drug QALYs
        num_points: Number of points in the curve (default 201 = 0.5% increments)

    Returns:
        Tuple of (discount_rates, icer_values) as numpy arrays
    """
    discount_rates = np.linspace(0, 1, num_points)
    icer_values = np.array([
        calculate_icer(c_drug_new, c_other_new, c_total_ref, q_new, q_ref, d)
        for d in discount_rates
    ])

    return discount_rates, icer_values


def calculate_scenario_results(scenario: ICERScenario) -> Dict:
    """
    Calculate comprehensive results for a scenario.

    Args:
        scenario: ICERScenario object with all inputs

    Returns:
        Dictionary with all calculated results
    """
    # Calculate derived values
    derived = calculate_derived_values(scenario)

    # Handle edge case
    if derived['delta_q'] == 0:
        return {
            'error': 'Invalid scenario: DeltaQ is zero (Q_new must differ from Q_ref)',
            'valid': False
        }

    # Calculate ICER at 0% discount
    icer_value = calculate_icer(
        scenario.c_drug_new, scenario.c_other_new, scenario.c_total_ref,
        scenario.q_new, scenario.q_ref, 0.0
    )

    # Calculate justified price
    justified_price = calculate_justified_price(
        scenario.c_other_new, scenario.c_total_ref,
        scenario.q_new, scenario.q_ref,
        scenario.icer_threshold
    )

    # Calculate elasticity
    elasticity = calculate_icer_elasticity(scenario.c_drug_new, derived['delta_q'])

    # Check cost-effectiveness
    cost_effective = is_cost_effective(icer_value, scenario.icer_threshold)

    return {
        'valid': True,

        # Input summary
        'c_drug_new': scenario.c_drug_new,
        'c_other_new': scenario.c_other_new,
        'c_total_new': derived['c_total_new'],
        'c_total_ref': scenario.c_total_ref,
        'q_new': scenario.q_new,
        'q_ref': scenario.q_ref,
        'icer_threshold': scenario.icer_threshold,

        # Calculated results
        'delta_q': derived['delta_q'],
        'delta_c': derived['delta_c'],
        'icer_value': icer_value,
        'justified_price': justified_price,
        'elasticity': elasticity,
        'cost_effective': cost_effective,

        # Additional metrics
        'price_difference': scenario.c_drug_new - justified_price,
        'price_ratio': scenario.c_drug_new / justified_price if justified_price > 0 else float('inf'),

        # Metadata
        'scenario_name': scenario.name,
        'description': scenario.description,
        'created_at': scenario.created_at
    }


def validate_inputs(c_drug_new: float, c_other_new: float, c_total_ref: float,
                   q_new: float, q_ref: float, icer_threshold: float) -> Tuple[bool, str]:
    """
    Validate input parameters.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for negative values
    if c_drug_new < 0:
        return False, "Drug cost cannot be negative"
    if c_other_new < 0:
        return False, "Other costs cannot be negative"
    if c_total_ref < 0:
        return False, "Reference total cost cannot be negative"
    if q_new < 0:
        return False, "New drug QALYs cannot be negative"
    if q_ref < 0:
        return False, "Reference drug QALYs cannot be negative"
    if icer_threshold <= 0:
        return False, "ICER threshold must be positive"

    # Check for zero QALYs difference
    if q_new == q_ref:
        return False, "New and reference QALYs must be different (DeltaQ cannot be zero)"

    # Check reasonable ranges
    if q_new > 50:
        return False, "New drug QALYs seems unreasonably high (>50 years)"
    if q_ref > 50:
        return False, "Reference drug QALYs seems unreasonably high (>50 years)"

    return True, ""


def compare_scenarios(scenarios: list[ICERScenario]) -> Dict:
    """
    Compare multiple scenarios and generate comparison metrics.

    Args:
        scenarios: List of ICERScenario objects

    Returns:
        Dictionary with comparison data
    """
    results = [calculate_scenario_results(s) for s in scenarios]
    valid_results = [r for r in results if r.get('valid', False)]

    if not valid_results:
        return {'error': 'No valid scenarios to compare'}

    comparison = {
        'num_scenarios': len(valid_results),
        'scenarios': valid_results,

        # Summary statistics
        'avg_icer': np.mean([r['icer_value'] for r in valid_results]),
        'min_icer': min(r['icer_value'] for r in valid_results),
        'max_icer': max(r['icer_value'] for r in valid_results),

        'avg_justified_price': np.mean([r['justified_price'] for r in valid_results]),
        'min_justified_price': min(r['justified_price'] for r in valid_results),
        'max_justified_price': max(r['justified_price'] for r in valid_results),

        # Count cost-effective scenarios
        'num_cost_effective': sum(r['cost_effective'] for r in valid_results),
        'pct_cost_effective': sum(r['cost_effective'] for r in valid_results) / len(valid_results) * 100
    }

    return comparison


def create_icer_discount_plot(scenarios, results=None) -> go.Figure:
    """
    Create an interactive Plotly visualization showing ICER across discount rates.
    Simple plot with discount rate (%) on Y-axis and ICER on X-axis.

    Args:
        scenarios: Either a single ICERScenario object or a list of ICERScenario objects
        results: Results dictionary (optional, not used in simple version)

    Returns:
        Plotly Figure object
    """
    # Handle both single scenario and multiple scenarios
    if isinstance(scenarios, list):
        scenario_list = scenarios
        is_multi_scenario = True
    else:
        scenario_list = [scenarios]
        is_multi_scenario = False

    # Define colors for different scenarios
    colors = [
        '#2563eb',  # Blue
        '#dc2626',  # Red
        '#16a34a',  # Green
        '#ca8a04',  # Yellow
        '#9333ea',  # Purple
        '#0891b2',  # Cyan
        '#ea580c',  # Orange
        '#be185d',  # Pink
        '#4b5563',  # Gray
        '#059669',  # Emerald
    ]

    # Generate discount rates from 0% to 100% in 0.5% increments
    discount_rates = np.arange(0, 1.005, 0.005)
    discount_pct = discount_rates * 100

    fig = go.Figure()
    max_positive_icer = 0.0

    # Plot each scenario
    for i, scenario in enumerate(scenario_list):
        color = colors[i % len(colors)]

        # Calculate ICER for each discount rate
        icer_values = np.array([
            calculate_icer(
                scenario.c_drug_new, scenario.c_other_new, scenario.c_total_ref,
                scenario.q_new, scenario.q_ref, d
            )
            for d in discount_rates
        ])

        max_positive_icer = max(max_positive_icer, float(np.max(icer_values)))

        scenario_name = scenario.name if hasattr(scenario, 'name') else f"Scenario {i+1}"
        
        # Main ICER vs Discount Rate curve
        fig.add_trace(go.Scatter(
            x=icer_values,
            y=discount_pct,
            mode='lines',
            name=scenario_name,
            line=dict(color=color, width=3 if not is_multi_scenario else 2),
            hovertemplate='<b>' + scenario_name + '</b><br><b>ICER:</b> £%{x:,.0f}/QALY<br><b>Discount:</b> %{y:.1f}%<extra></extra>'
        ))

    # Update layout
    title_text = f'<b>ICER vs Discount Rate</b><br><sub>{len(scenario_list)} scenario{"s" if len(scenario_list) > 1 else ""}</sub>' if is_multi_scenario else f'<b>ICER vs Discount Rate</b><br><sub>{scenario_list[0].name}</sub>'
    x_axis_max = max(max_positive_icer, 1.0)

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=18, color='#1e293b', family='Inter, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(
                text='<b>ICER (£/QALY)</b>',
                font=dict(size=14, color='#1e293b', family='Inter, sans-serif')
            ),
            range=[0, x_axis_max],
            tickfont=dict(size=12, color='#64748b'),
            gridcolor='#e2e8f0',
            tickformat='£,.0f',
            showline=True,
            linewidth=2,
            linecolor='#cbd5e1'
        ),
        yaxis=dict(
            title=dict(
                text='<b>Discount Rate (%)</b>',
                font=dict(size=14, color='#1e293b', family='Inter, sans-serif')
            ),
            tickfont=dict(size=12, color='#64748b'),
            gridcolor='#e2e8f0',
            tickformat='.0f',
            showline=True,
            linewidth=2,
            linecolor='#cbd5e1'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='right',
            x=0.99,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#cbd5e1',
            borderwidth=1,
            font=dict(size=10 if is_multi_scenario else 11, family='Inter, sans-serif')
        ),
        margin=dict(l=80, r=40, t=80, b=60),
        height=500
    )

    return fig
