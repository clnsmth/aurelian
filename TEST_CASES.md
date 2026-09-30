# Manual Test Cases: Aurelian (Personalized Development)

This document provides a structured suite of manual test cases for verifying personalized local development on Aurelian. It focuses on command-line workflows, Google Gemini model integration, Pydantic AI 2.x compatibility, and agent-specific tool execution.

---

## 1. Environment & Prerequisites

Before running the manual tests, ensure your local environment is configured:

1. **Virtual Environment & Dependencies**:
   Ensure dependencies are synchronized with [uv](https://docs.astral.sh/uv/):
   ```bash
   uv sync
   ```

2. **Required Environment Variables**:
   ```bash
   # Required for Google Gemini native testing
   export GEMINI_API_KEY="your-gemini-api-key"

   # Disable mandatory Logfire cloud authentication prompts
   export LOGFIRE_SEND_TO_LOGFIRE=false

   # Optional: Suppress Pydantic AI terminal ASCII banners
   export PYDANTIC_AI_NO_BANNER=1
   ```

3. **Optional (OpenAI / Proxy Endpoint Testing)**:
   ```bash
   # If testing Google Gemini via the OpenAI-compatible endpoint
   export OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
   export OPENAI_API_KEY="$GEMINI_API_KEY"
   ```

---

## 2. Test Execution Tracking

| Test ID | Category | Target / Description | Model Tested | Status | Last Run Date | Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `TC-ENV-01` | Environment | CLI Help & Entry Point | N/A | Pass | 2026-09-29 | Validates CLI loads without Gradio |
| `TC-ENV-02` | Environment | Logfire Auth Bypass | N/A | Pass | 2026-09-29 | `LOGFIRE_SEND_TO_LOGFIRE=false` |
| `TC-MOD-01` | Model Routing | Bare Gemini Model Aliasing | `gemini-2.0-flash` | Pass | 2026-09-29 | Auto-resolves `google:` prefix |
| `TC-MOD-02` | Model Routing | Explicit Provider Prefix | `google:gemini-2.0-flash`| Pass | 2026-09-29 | Direct GoogleModel inference |
| `TC-MOD-03` | Model Routing | Gemini Reasoning / Thinking | `gemini-2.5-flash` | Untested | — | Verifies `thought_signature` |
| `TC-MOD-04` | Model Routing | OpenAI-Compatible Proxy | `openai:gemini-2.0-flash`| Pass | 2026-09-29 | Routes to OpenAI endpoint |
| `TC-MOD-05` | Model Routing | Built-in Test Provider | `test` | Pass | 2026-09-29 | Mock agent execution |
| `TC-AGT-01` | Agent - Diagnosis | Single Disease Lookup | `gemini-2.0-flash` | Untested | — | MONDO disease ID & phenotypes |
| `TC-AGT-02` | Agent - Diagnosis | Multi-phenotype Query | `gemini-2.0-flash` | Untested | — | Diagnostic differential |
| `TC-AGT-03` | Agent - Mapper | Ontology Term Mapping | `gemini-2.0-flash` | Untested | — | OBO ontology term lookup |
| `TC-AGT-04` | Agent - Gene | Gene Info & Summary | `gemini-2.0-flash` | Untested | — | Gene annotation retrieval |
| `TC-AGT-05` | Agent - Monarch | Biomedical Entity Search | `gemini-2.0-flash` | Untested | — | Monarch KG queries |

---

## 3. Test Cases

### Category: Environment & Baseline (`ENV`)

#### `TC-ENV-01`: CLI Help & Entry Point
- **Objective**: Verify that the Aurelian CLI loads cleanly from the virtual environment without requiring Gradio or Starlette.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false uv run aurelian --help
  ```
- **Expected Output**:
  - Exits with returncode `0`.
  - Displays the command group overview and subcommands (`diagnosis`, `mapper`, `gene`, etc.).
  - No `ModuleNotFoundError` for `gradio` or `starlette`.

#### `TC-ENV-02`: Logfire Authentication Bypass
- **Objective**: Verify that running commands does not prompt for interactive browser login to Logfire when `LOGFIRE_SEND_TO_LOGFIRE=false` is set.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false uv run aurelian --version
  ```
- **Expected Output**:
  - Displays current version (e.g. `aurelian, version 0.4.3`).
  - No blocking authentication URLs or credential warnings.

---

### Category: Model Providers & Routing (`MOD`)

#### `TC-MOD-01`: Bare Gemini Model Aliasing
- **Objective**: Verify that passing a bare Gemini model name (e.g. `gemini-2.0-flash`) is automatically translated to `google:gemini-2.0-flash` via the compatibility layer in [`src/aurelian/__init__.py`](file:///Users/csmith/Code/clnsmth/aurelian/src/aurelian/__init__.py).
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run python -c "
  import aurelian
  from pydantic_ai.models import infer_model
  m = infer_model('gemini-2.0-flash')
  print(type(m).__name__, m.model_name)
  "
  ```
- **Expected Output**:
  - Outputs `GoogleModel gemini-2.0-flash`.
  - Does NOT throw `pydantic_ai.exceptions.UserError: Unknown model: gemini-2.0-flash`.

#### `TC-MOD-02`: Explicit Google Provider Prefix
- **Objective**: Verify that specifying the model with the canonical provider prefix `google:` functions identically.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run python -c "
  import aurelian
  from pydantic_ai.models import infer_model
  m = infer_model('google:gemini-2.0-flash')
  print(type(m).__name__, m.model_name)
  "
  ```
- **Expected Output**:
  - Outputs `GoogleModel gemini-2.0-flash`.

#### `TC-MOD-03`: Gemini Reasoning Model (`thought_signature` handling)
- **Objective**: Verify that models with thinking/reasoning capabilities (such as `gemini-2.5-flash`) can execute multi-turn tool calls without failing on missing `thought_signature`.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian diagnosis --model gemini-2.5-flash "What are the common clinical features of Marfan syndrome?"
  ```
- **Expected Output**:
  - Model calls ontology and phenotype tools across turns.
  - Returns a coherent diagnostic summary referencing MONDO / HPO identifiers.
  - Does NOT raise `google.genai.errors.ClientError: 400 INVALID_ARGUMENT. Function call is missing a thought_signature`.

#### `TC-MOD-04`: OpenAI-Compatible Proxy Route
- **Objective**: Verify that Pydantic AI's `OpenAIChatModel` can route Gemini models through Google's OpenAI-compatible endpoint.
- **Command**:
  ```bash
  OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/" \
  OPENAI_API_KEY="$GEMINI_API_KEY" \
  LOGFIRE_SEND_TO_LOGFIRE=false \
  uv run aurelian diagnosis --model openai:gemini-2.0-flash "What is the MONDO ID for Marfan syndrome?"
  ```
- **Expected Output**:
  - Outputs diagnosis result identifying `MONDO:0007947`.
  - Invokes `pydantic_ai.models.openai` instead of native Google GenAI SDK.

#### `TC-MOD-05`: Built-in Test Provider
- **Objective**: Verify that the built-in offline test provider runs without external network calls or credentials.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false uv run python -c "
  import aurelian
  from pydantic_ai import Agent
  a = Agent('test')
  res = a.run_sync('ping')
  print(res.data)
  "
  ```
- **Expected Output**:
  - Outputs `success (no tool calls)` via the `.data` backwards-compatibility alias.

---

### Category: Agent Execution (`AGT`)

#### `TC-AGT-01`: Diagnosis Agent — Single Disease Lookup
- **Objective**: Test the Diagnosis Agent using MONDO lookup tools to identify disease details.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian diagnosis --model gemini-2.0-flash "What is the MONDO ID for Ehlers-Danlos syndrome classic type 1?"
  ```
- **Expected Output**:
  - Output contains the correct MONDO identifier (e.g., `MONDO:0007523` / classic Ehlers-Danlos syndrome).
  - Clear narrative explanation with tool references.

#### `TC-AGT-02`: Diagnosis Agent — Patient Phenotype Differential
- **Objective**: Test the agent's ability to analyze multiple phenotypic signs and provide a differential diagnosis.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian diagnosis --model gemini-2.0-flash \
  "Patient has tall stature, ectopia lentis, aortic root dilation, and arachnodactyly. What is the most likely diagnosis and MONDO ID?"
  ```
- **Expected Output**:
  - Identifies Marfan syndrome (`MONDO:0007947`) as the primary diagnosis.
  - Lists relevant HPO phenotype associations.

#### `TC-AGT-03`: Ontology Mapper Agent — Search & Preprocessing
- **Objective**: Test ontology term mapping for anatomical and phenotype terms.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian ontology-mapper --model gemini-2.0-flash "Find ontology terms for hepatomegaly and liver parenchyma"
  ```
- **Expected Output**:
  - Maps terms to relevant ontologies (e.g., HP for `hepatomegaly`, UBERON for `liver parenchyma`).
  - Returns IDs with standard CURIE prefixes.

#### `TC-AGT-04`: Gene Agent — Gene Search & Functional Context
- **Objective**: Test gene symbol queries and functional summary extraction.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian gene --model gemini-2.0-flash "FBN1"
  ```
- **Expected Output**:
  - Summary of the *FBN1* (Fibrillin 1) gene.
  - References its role in Marfan syndrome and connective tissue formation.

#### `TC-AGT-05`: Monarch Agent — Biomedical Entity Associations
- **Objective**: Query Monarch Initiative knowledge graph for disease-to-phenotype or disease-to-gene associations.
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian monarch --model gemini-2.0-flash "What genes are associated with osteogenesis imperfecta?"
  ```
- **Expected Output**:
  - Mentions key collagen genes (*COL1A1*, *COL1A2*, etc.).
  - Returns structured disease-gene associations.

---

## 4. Template for Adding New Test Cases

Copy and paste this template when adding new manual test scenarios:

```markdown
#### `TC-XXX-NN`: [Test Title]
- **Objective**: [Clear statement of what behavior or edge-case is being verified]
- **Target Agent / Component**: [e.g., diagnosis, linkml, pydantic-ai shim]
- **Prerequisites / Environment**: [e.g., GEMINI_API_KEY, network access]
- **Command**:
  ```bash
  LOGFIRE_SEND_TO_LOGFIRE=false GEMINI_API_KEY="$GEMINI_API_KEY" \
  uv run aurelian <agent-name> --model <model> "<query>"
  ```
- **Expected Output**:
  - [Specific expected content, CURIEs, or responses]
  - [Negative check: what errors must NOT occur]
- **Actual Result**: [Record output upon manual verification]
- **Status**: [Untested | Pass | Fail | Blocked]
- **Notes**: [Any anomalies, token counts, or performance observations]
```
