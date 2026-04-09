"""Simulation and cost estimation tools."""

import json

from langchain_core.tools import tool


@tool
def simulate_experiment(protocol_json: str, parameters_json: str = "{}") -> str:
    """Simulate an experiment and predict likely outcomes based on protocol + parameters.

    Uses known biology heuristics and memory context to predict outcomes.
    This is a reasoning scaffold — the LLM agent fills in the scientific reasoning.

    Args:
        protocol_json: JSON describing the protocol (assay_type, steps, reagents).
        parameters_json: JSON with parameter overrides.

    Returns:
        Structured prediction of expected outcomes, potential failure modes, and confidence.
    """
    try:
        protocol = json.loads(protocol_json)
        params = json.loads(parameters_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    assay_type = protocol.get("assay_type", "generic")
    steps = protocol.get("steps", [])
    reagents = protocol.get("reagents", [])

    # Build a structured reasoning prompt for the agent to respond to
    return (
        f"Simulate this {assay_type} experiment:\n"
        f"Steps: {len(steps)} steps\n"
        f"Reagents: {', '.join(reagents) if reagents else 'not specified'}\n"
        f"Parameter overrides: {params}\n\n"
        "Predict:\n"
        "1. Expected outcome (with confidence 0-1)\n"
        "2. Top 3 failure modes and their likelihood\n"
        "3. Critical parameters that most affect outcome\n"
        "4. Suggested controls\n"
        "Base predictions on biological principles and any recalled prior experiments."
    )


@tool
def estimate_cost(reagents_json: str) -> str:
    """Estimate experiment cost from a reagent list.

    Args:
        reagents_json: JSON array of reagent objects with optional 'unit_cost' and 'quantity'.
            Example: [{"name": "Anti-CD3", "unit_cost": 450, "quantity": 1}, ...]

    Returns:
        Itemized cost breakdown and total estimate.
    """
    try:
        reagents = json.loads(reagents_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    # Default unit costs for common reagent categories (rough estimates in USD)
    _CATEGORY_DEFAULTS: dict[str, float] = {
        "antibody": 350.0,
        "enzyme": 150.0,
        "buffer": 50.0,
        "cell": 200.0,
        "kit": 500.0,
        "media": 80.0,
        "chemical": 100.0,
    }

    if not isinstance(reagents, list):
        return "Expected a JSON array of reagent objects."

    total = 0.0
    lines = ["**Cost Estimate:**"]
    for r in reagents:
        name = r.get("name", "Unknown")
        unit_cost = float(r.get("unit_cost", 0))
        quantity = float(r.get("quantity", 1))

        if unit_cost == 0:
            # Guess from category if provided
            category = r.get("category", "").lower()
            unit_cost = _CATEGORY_DEFAULTS.get(category, 100.0)
            lines.append(f"  {name}: ${unit_cost:.2f} × {quantity:.1f} = ${unit_cost * quantity:.2f} (estimated)")
        else:
            lines.append(f"  {name}: ${unit_cost:.2f} × {quantity:.1f} = ${unit_cost * quantity:.2f}")

        total += unit_cost * quantity

    lines.append(f"\n**Total: ${total:.2f} USD**")
    lines.append("_Note: Costs are estimates. Verify against current vendor pricing._")
    return "\n".join(lines)
