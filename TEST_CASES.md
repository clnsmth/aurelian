# Manual Test Cases: Aurelian Development

This document tracks manual test cases for customized local development on Aurelian.

---

## Test Case 1: ENVO Ontology Mapping for MIxS Environmental Context & Processes

### 1. Objective
Verify that Aurelian's ontology mapper correctly extracts and ranks terms from the **Environment Ontology (ENVO)** across five key environmental dimensions (three standardized [MIxS](https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS) environmental context tiers plus two major process categories) based on study metadata, abstract, and methods text.

### 2. Category Definitions & Requirements
1. **Broad-Scale Environmental Context (`env_broad_scale`)**:
   - **Definition**: The major environmental system the sample or specimen came from. Must have a coarse spatial grain to provide the general environmental context of where the sampling occurred (e.g., in a desert or rainforest).
   - **Constraint**: Must be a subclass of EnvO's biome class: [`ENVO:00000428`](http://purl.obolibrary.org/obo/ENVO_00000428).
2. **Local Environmental Context (`env_local_scale`)**:
   - **Definition**: The entity or entities in the sample or specimen's local vicinity that have significant causal influences on the sample or specimen. Smaller spatial grain than `env_broad_scale`.
   - **Constraint**: EnvO terms representing environmental features, sites, or landforms (e.g., lake, kettle lake, shore, littoral zone).
3. **Environmental Medium (`env_medium`)**:
   - **Definition**: The environmental material(s) immediately surrounding the sample or specimen at the time of sampling.
   - **Constraint**: Must be a subclass of 'environmental material' ([`ENVO:00010483`](http://purl.obolibrary.org/obo/ENVO_00010483)). Must be mass/volume nouns (e.g., water, lake water, freshwater) and NOT discrete, countable entities.
4. **Environmental System Process (`[placeholder: env_system_process]`)**:
   - **Definition**: Major natural, physical, geological, or hydrological processes occurring in the system described in the text (e.g. glacial formation/deposition, water depth fluctuations, seasonal hydrological cycle).
   - **Constraint**: Must be a subclass of 'environmental system process' ([`ENVO:02500000`](http://purl.obolibrary.org/obo/ENVO_02500000)).
5. **Anthropogenic Modulatory Intervention Process (`[placeholder: env_intervention_process]`)**:
   - **Definition**: Major human actions, management practices, or intentional interventions that monitor, modulate, or conserve the environmental system described in the text (e.g. municipal watershed management, biodiversity conservation/monitoring, ecological survey).
   - **Constraint**: Must be a subclass of 'anthropogenic modulatory intervention process' ([`ENVO:02500026`](http://purl.obolibrary.org/obo/ENVO_02500026)).

---

### 3. Test Inputs

- **Abstract**:
  > This data package contains survey data beginning in 2002 for amphibian egg masses in five small kettle lakes (known as "14 Lakes") in the Cedar River Municipal Watershed, located in King County, Washington, USA. These surveys are conducted annually and are intended to be continued. The lakes range in size from 0.8 to 4.3 acres, have no perennial inlet or outlet, and were formed through glacial outwash deposits. The lakes are located at an elevation of 800 feet and are well suited for pond breeding amphibians because the lakes have no fish. Surveys were conducted annually, typically during the last week of March or first week of April, to coincide with amphibian breeding seasons. Surveyors walked, waded, or paddled the perimeter of each of the lakes during a survey, and tallied the number and type of egg masses that were encountered. Red legged frogs (Rana aurora) were of specific interest for the surveys, though egg masses of other species were noted during some survey years. The lakes represent the largest known breeding concentration of red legged frogs in the municipal watershed. The water depth of the lakes fluctuates year-to-year, which affected the feasibility of surveys. Lower water levels correspond to easier survey conditions: steep slopes and thick vegetation make surveying challenging when the water is high. Surveys were periodically cancelled during years where high water made surveying difficult or during staffing shortages. Counts of red legged frog egg masses across all lakes ranged between 24 and 1778 in a given year.

- **Methods**:
  ```xml
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
  ```

---

### 4. Execution

- **Target Script**: [`scripts/extract_envo_context.py`](file:///Users/csmith/Code/clnsmth/aurelian/scripts/extract_envo_context.py)
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false PYDANTIC_AI_NO_BANNER=1 GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run python scripts/extract_envo_context.py --model gemini-3.8-flash
  ```

---

### 5. Expected Output & Acceptance Criteria

1. **Category Coverage**: Must return top-ranking ENVO terms for all five categories (broad scale, local scale, medium, environmental process, and intervention process).
2. **Taxonomic Integrity**:
   - `env_broad_scale` must resolve to an aquatic or terrestrial biome (subclass of `ENVO:00000428`).
   - `env_local_scale` must resolve to a specific lake or shoreline environmental entity (e.g., freshwater lake, kettle, lake shore, littoral zone).
   - `env_medium` must resolve to a mass/volume water material (subclass of `ENVO:00010483`).
   - `[placeholder: env_system_process]` must resolve to an environmental or hydrological system process (subclass of `ENVO:02500000`).
   - `[placeholder: env_intervention_process]` must resolve to an intentional human intervention, monitoring, or conservation process (subclass of `ENVO:02500026`).
3. **Execution Stability**:
   - Must use local OAK SQLite cache (`~/.data/oaklib/envo.db`) without throwing S3 HTTP 403 Forbidden errors.
   - Must handle multi-turn tool calling within configured request limits.
4. **Provenance**:
   - Outputs must provide valid Bioregistry links (`https://bioregistry.io/ENVO:...`).

---

### 6. Verified Results

| Category / Predicate | ENVO Term ID | Term Label | Match Type / Confidence | Bioregistry Link |
| :--- | :--- | :--- | :--- | :--- |
| **`env_broad_scale`** | `ENVO:01000252` | freshwater lake biome | Exact / High | [ENVO:01000252](https://bioregistry.io/ENVO:01000252) |
| **`env_local_scale`** | `ENVO:00000311` | kettle | Exact / High | [ENVO:00000311](https://bioregistry.io/ENVO:00000311) |
| **`env_medium`** | `ENVO:04000007` | lake water | Exact / High | [ENVO:04000007](https://bioregistry.io/ENVO:04000007) |
| **`[placeholder: env_system_process]`** | `ENVO:02500031` | hydrological process | Semantic / High | [ENVO:02500031](https://bioregistry.io/ENVO:02500031) |
| **`[placeholder: env_intervention_process]`** | `ENVO:02500041` | environmental monitoring | Exact / High | [ENVO:02500041](https://bioregistry.io/ENVO:02500041) |

#### Detailed Term Provenance & Rationale:
- **`env_broad_scale`**: `ENVO:01000252` (`freshwater lake biome`) is a direct subclass of `ENVO:00000428` (`biome` &rarr; `aquatic biome` &rarr; `freshwater biome` &rarr; `freshwater lake biome`). (Alternative regional terrestrial biome: `ENVO:01000211` `temperate coniferous forest biome`).
- **`env_local_scale`**: `ENVO:00000311` (`kettle`) directly matches the kettle depressions explicitly cited in the abstract ("formed through glacial outwash deposits"). Related local entities include `ENVO:00000021` (`freshwater lake`), `ENVO:00000382` (`lake shore`), and `ENVO:01000407` (`littoral zone`).
- **`env_medium`**: `ENVO:04000007` (`lake water`) is a mass noun subclass of `ENVO:00010483` (`environmental material` &rarr; `water` &rarr; `fresh water` &rarr; `lake water`), describing the liquid medium surrounding the submerged egg masses.
- **`[placeholder: env_system_process]`**: `ENVO:02500031` (`hydrological process`) is a direct subclass of `ENVO:02500000` (`environmental system process`), capturing the annual water depth fluctuations that connect or isolate the lakes. Geological formation process: `ENVO:01001655` (`glacial process`).
- **`[placeholder: env_intervention_process]`**: `ENVO:02500041` (`environmental monitoring`) is a direct subclass of `ENVO:02500026` (`anthropogenic modulatory intervention process`), representing the ongoing annual amphibian egg mass surveillance program within the municipal watershed.

- **Status**: **PASS** (Verified with `gemini-3.8-flash` on 2026-09-30)
