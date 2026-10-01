#!/usr/bin/env python3
"""
Extract ENVO ontology terms for MIxS environmental context tiers and process categories.

This script uses Aurelian's Ontology Mapper agent to analyze study abstract and methods
text and identify top candidate terms from the Environment Ontology (ENVO) for five
categories:
1. env_broad_scale: Major environmental system / biome (coarse spatial grain, subclasses of ENVO:00000428)
2. env_local_scale: Local vicinity entities with causal influence (finer spatial grain)
3. env_medium: Environmental material immediately surrounding specimen (subclasses of ENVO:00010483)
4. [placeholder: env_system_process]: Natural/environmental processes (subclasses of ENVO:02500000)
5. [placeholder: env_intervention_process]: Anthropogenic modulatory interventions (subclasses of ENVO:02500026)
"""

import argparse
import os
import sys
from typing import Optional

# Ensure aurelian is loaded to register pydantic-ai 2.x backward compatibility shims
import aurelian  # noqa: F401
from pydantic_ai import UsageLimits
from pydantic_ai.settings import ModelSettings
from aurelian.agents.ontology_mapper.ontology_mapper_agent import ontology_mapper_agent
from aurelian.agents.ontology_mapper.ontology_mapper_config import OntologyMapperDependencies

DEFAULT_ABSTRACT = """
This data package contains survey data beginning in 2002 for amphibian egg masses in
five small kettle lakes (known as "14 Lakes") in the Cedar River Municipal Watershed,
located in King County, Washington, USA. These surveys are conducted annually and are
intended to be continued. The lakes range in size from 0.8 to 4.3 acres, have no perennial
inlet or outlet, and were formed through glacial outwash deposits. The lakes are located at
an elevation of 800 feet and are well suited for pond breeding amphibians because the lakes
have no fish. Surveys were conducted annually, typically during the last week of March or
first week of April, to coincide with amphibian breeding seasons. Surveyors walked, waded,
or paddled the perimeter of each of the lakes during a survey, and tallied the number and
type of egg masses that were encountered. Red legged frogs (Rana aurora) were of specific
interest for the surveys, though egg masses of other species were noted during some survey
years. The lakes represent the largest known breeding concentration of red legged frogs in
the municipal watershed. The water depth of the lakes fluctuates year-to-year, which
affected the feasibility of surveys. Lower water levels correspond to easier survey
conditions: steep slopes and thick vegetation make surveying challenging when the water is
high. Surveys were periodically cancelled during years where high water made surveying
difficult or during staffing shortages. Counts of red legged frog egg masses across all
lakes ranged between 24 and 1778 in a given year.
""".strip()

DEFAULT_METHODS = """
<methods>
  <methodStep>
    <description>
      <para>Surveys are typically conducted during the last week of March or first week of April
        in fair weather that allows for counting egg masses beneath the water surface.</para>
    </description>
  </methodStep>
  <methodStep>
    <description>
      <para>Surveyors walk around the perimeter of the lake shore, counting every
        amphibian egg mass that they encounter. If amphibians in other life stages are
        encountered, the surveyor may also note them.</para>
    </description>
  </methodStep>
  <methodStep>
    <description>
      <para>Surveyors either walk around the lake shore, or wade around the lake shore,
        depending on the water depth of the lake (which fluctuates year-to-year), or the depth
        of the amphibian egg masses. Some years this can be very challenging when the water
        level is high enough due to dense vegetation and steep banks. High water levels caused
        surveyors to cancel the survey in some years.</para>
    </description>
  </methodStep>
  <methodStep>
    <description>
      <para>Depending on the water level, big lake and deep lake are either one continuous water
        body, or two distinct lakes. These were either counted together as one water body or
        distinctly as two water bodies depending on the surveyor, not whether or not they were a
        continuous water body during that year. Earlier surveys count these as two distinct
        lakes, and later surveys count these distinctly when they are separated, and as one lake
        when they are connected.</para>
    </description>
  </methodStep>
  <methodStep>
    <description>
      <para>In 2012 surveyors experimented with surveying a portion of the big lake and deep
        lake complex by snorkeling instead of walking to cope with the high water levels.</para>
    </description>
  </methodStep>
  <methodStep>
    <description>
      <para>Beginning in 2022 surveyors also surveyed select lakes via canoe to examine whether
        it was more effective for counting masses in deeper water. Surveyors continued to survey
        lakes on foot for comparison across years.</para>
    </description>
  </methodStep>
</methods>
""".strip()

PROMPT_TEMPLATE = """
Please analyze the provided study abstract and methods to identify and map the highest matching
terms from the ENVO (Environment Ontology) across the following five categories (three standardized
MIxS environmental context categories plus two major process categories):

## 1. Broad-Scale Environmental Context (`env_broad_scale`)
- **Definition**: The major environmental system the sample or specimen came from. Coarse spatial grain
  providing general environmental context (e.g. desert, rainforest).
- **Recommended Range**: Subclasses of EnvO's biome class: `ENVO:00000428` (http://purl.obolibrary.org/obo/ENVO_00000428).
- **Guidelines**: See https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS

## 2. Local Environmental Context (`env_local_scale`)
- **Definition**: Entity or entities in the sample or specimen's local vicinity having significant causal
  influences on the specimen. Smaller spatial grain than `env_broad_scale`.
- **Recommended Range**: EnvO terms representing environmental features, sites, or landforms (e.g., lake, kettle lake, shore, littoral zone).
- **Guidelines**: See https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS

## 3. Environmental Medium (`env_medium`)
- **Definition**: The environmental material(s) immediately surrounding the sample or specimen at sampling time.
- **Recommended Range**: Subclasses of 'environmental material' (`ENVO:00010483`). Must be mass/volume nouns
  (e.g. freshwater, lake water, surface water) and NOT discrete countable entities.
- **Guidelines**: See https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS

## 4. Environmental System Process (`[placeholder: env_system_process]`)
- **Definition**: Major natural, physical, geological, or hydrological processes occurring in the system described
  in the text (e.g. glacial formation/deposition, water depth fluctuation, seasonal hydrological cycle).
- **Recommended Range**: Subclasses of 'environmental system process' (`ENVO:02500000`, http://purl.obolibrary.org/obo/ENVO_02500000).

## 5. Anthropogenic Modulatory Intervention Process (`[placeholder: env_intervention_process]`)
- **Definition**: Major human actions, management practices, or intentional interventions that monitor, modulate,
  or conserve the environmental system described in the text (e.g. municipal watershed management, biodiversity conservation/monitoring, ecological survey).
- **Recommended Range**: Subclasses of 'anthropogenic modulatory intervention process' (`ENVO:02500026`, http://purl.obolibrary.org/obo/ENVO_02500026).

---

### Study Abstract:
{abstract}

### Study Methods:
{methods}

---

### Instructions:
1. Use the `search_terms` tool with ontology_id="envo" to search for and verify candidate terms in ENVO. Focus on direct ontology searches (e.g. biomes, freshwater features, water materials, hydrological/geological processes, and environmental monitoring/ecosystem management terms) and minimize unnecessary web search calls.
2. For each of the five categories, present the best matching term(s).
3. Include for each match:
   - **Category / Predicate**: (`env_broad_scale`, `env_local_scale`, `env_medium`, `[placeholder: env_system_process]`, or `[placeholder: env_intervention_process]`)
   - **ENVO Term ID**: (e.g. `ENVO:00000021`)
   - **Label**: (e.g. `freshwater lake`)
   - **Bioregistry Link**: (e.g. `https://bioregistry.io/ENVO:00000021`)
   - **Match Type / Confidence**: (Exact, Partial, Semantic)
   - **Rationale**: Explain why this term was selected based on the study text, category definitions, and root class hierarchy.
4. Format the final summary as a clean 5-row Markdown table followed by detailed profiles for each category.
"""


def extract_envo_context(
    abstract: str = DEFAULT_ABSTRACT,
    methods: str = DEFAULT_METHODS,
    model: str = "gemini-3.8-flash",
    effort: Optional[str] = None,
    ontologies: Optional[list] = None,
) -> tuple[str, Optional[object]]:
    """Run the ontology mapper agent to extract ENVO context.

    Args:
        abstract: Study abstract text
        methods: Study methods text
        model: Model identifier (e.g., gemini-3.8-flash, gemini-2.5-pro)
        effort: Reasoning/thinking effort level ('minimal', 'low', 'medium', 'high', 'xhigh')
        ontologies: List of ontologies to search (defaults to ['envo'])

    Returns:
        Tuple of (output_markdown_string, run_usage_object)
    """
    if ontologies is None:
        ontologies = ["envo"]

    # Configure dependencies restricted to ENVO
    deps = OntologyMapperDependencies(
        max_search_results=30,
        ontologies=ontologies,
    )

    prompt = PROMPT_TEMPLATE.format(abstract=abstract, methods=methods)

    # Run the agent synchronously with generous limits for multi-category ontology search
    run_kwargs = {
        "deps": deps,
        "usage_limits": UsageLimits(request_limit=120),
    }
    if model:
        run_kwargs["model"] = model
    if effort:
        run_kwargs["model_settings"] = ModelSettings(thinking=effort)

    result = ontology_mapper_agent.run_sync(prompt, **run_kwargs)
    text_output = result.data if hasattr(result, "data") else result.output
    usage = getattr(result, "usage", None)
    return text_output, usage


def main():
    parser = argparse.ArgumentParser(
        description="Extract ENVO ontology terms for MIxS environmental context categories."
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AURELIAN_MODEL", "gemini-3.8-flash"),
        help="Model identifier (default: gemini-3.8-flash)",
    )
    parser.add_argument(
        "--effort",
        type=str,
        choices=["minimal", "low", "medium", "high", "xhigh"],
        default=None,
        help="Reasoning/thinking effort level for Gemini models: minimal, low, medium, high, xhigh (optional)",
    )
    parser.add_argument(
        "--abstract-file",
        type=str,
        default=None,
        help="Path to file containing study abstract text (optional)",
    )
    parser.add_argument(
        "--methods-file",
        type=str,
        default=None,
        help="Path to file containing study methods text (optional)",
    )
    args = parser.parse_args()

    abstract = DEFAULT_ABSTRACT
    if args.abstract_file:
        with open(args.abstract_file, "r", encoding="utf-8") as f:
            abstract = f.read().strip()

    methods = DEFAULT_METHODS
    if args.methods_file:
        with open(args.methods_file, "r", encoding="utf-8") as f:
            methods = f.read().strip()

    effort_str = f" (effort: {args.effort})" if args.effort else ""
    print(f"Extracting ENVO terms using model: {args.model}{effort_str}")
    print("Categories: env_broad_scale, env_local_scale, env_medium, env_system_process, env_intervention_process")
    print("=" * 60)

    try:
        output, usage = extract_envo_context(
            abstract=abstract,
            methods=methods,
            model=args.model,
            effort=args.effort,
        )
        print("\n" + output)

        if usage:
            print("\n" + "=" * 60)
            print("Usage Metrics:")
            print(f"  Requests: {getattr(usage, 'requests', 'N/A')}")
            print(f"  Input Tokens: {getattr(usage, 'input_tokens', 'N/A')}")
            print(f"  Output Tokens: {getattr(usage, 'output_tokens', 'N/A')}")
            reasoning_tokens = getattr(usage, "output_reasoning_tokens", None)
            if reasoning_tokens is not None:
                print(f"  Reasoning Tokens: {reasoning_tokens}")
            details = getattr(usage, "details", None)
            if details and isinstance(details, dict):
                thoughts = details.get("thoughts_tokens")
                if thoughts is not None:
                    print(f"  Thought Tokens: {thoughts}")
    except Exception as e:
        print(f"Error during ENVO extraction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
