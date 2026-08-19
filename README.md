# ScenePilot

**AI-Assisted Screenplay Analysis and Production Intelligence Platform**

ScenePilot is a production intelligence system that analyzes screenplay documents and converts unstructured screenplay content into structured information that can support pre-production research and planning.

The system is designed around a document-processing pipeline that combines screenplay parsing, structured extraction, AI-assisted analysis, and a web-based interface for reviewing the resulting production intelligence.

---

## Overview

A screenplay contains information required for production planning, but much of it is embedded in free-form text rather than structured data.

ScenePilot processes a screenplay and extracts information such as:

* Scenes and scene boundaries
* Scene headings
* Locations
* Interior/exterior classification
* Time of day
* Characters appearing in scenes
* Scene descriptions
* Production-related details
* Location and scene-level intelligence

The extracted information is then normalized into structured data and presented through a web interface.

The primary objective is to reduce the amount of manual screenplay breakdown required during the research and pre-production stages.

---

# System Pipeline

The core ScenePilot workflow can be represented as:

```text
                    ┌─────────────────────┐
                    │    Screenplay       │
                    │  PDF / Document     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Document Input    │
                    │   & Validation      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Text Extraction    │
                    │  / Document Parsing │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Screenplay Parsing  │
                    │                     │
                    │ • Scene headings    │
                    │ • Action            │
                    │ • Dialogue          │
                    │ • Characters        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ AI-Assisted         │
                    │ Analysis            │
                    │                     │
                    │ • Scene intelligence│
                    │ • Character data   │
                    │ • Location data    │
                    │ • Production data  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Structured         │
                    │ Production Data    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Production         │
                    │ Intelligence       │
                    │ Processing         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Web Dashboard      │
                    │ & Research View    │
                    └─────────────────────┘
```

---

# Processing Pipeline

## 1. Screenplay Input

The pipeline begins with a screenplay supplied by the user.

The uploaded document is treated as the source of truth for the analysis. Before processing, the application validates the input and prepares the document for extraction.

The system is intended to support screenplay documents where scene structure, dialogue, action, and character information can be identified from the document.

---

## 2. Text Extraction

The screenplay document is converted into machine-readable text.

At this stage, the system separates the document-processing problem from the analysis problem.

```text
Document
   │
   ▼
Text Extraction
   │
   ▼
Raw Screenplay Text
```

The extracted text is subsequently passed to the screenplay parsing stage.

This separation makes the pipeline easier to extend to additional document formats and extraction methods.

---

## 3. Screenplay Parsing

Raw screenplay text is not immediately treated as production data.

The parser identifies screenplay-specific structures, including:

```text
Scene Heading
      │
      ├── Location
      ├── INT / EXT
      └── Time of Day

Action
      │
      └── Scene Description

Character
      │
      └── Dialogue

Transition / Formatting
```

The purpose of this stage is to establish the structural context required for downstream analysis.

For example, a scene heading such as:

```text
INT. POLICE STATION - NIGHT
```

can be represented as:

```json
{
  "scene": 12,
  "type": "INT",
  "location": "POLICE STATION",
  "time": "NIGHT"
}
```

This structured representation provides a consistent input for the intelligence layer.

---

# 4. AI-Assisted Analysis

After the screenplay has been structurally parsed, relevant screenplay information is passed through the AI analysis layer.

The AI layer is responsible for interpreting information that cannot reliably be obtained through simple formatting or rule-based extraction alone.

Depending on the analysis being performed, this can include:

* Identifying production-relevant entities
* Understanding scene context
* Associating characters with scenes
* Interpreting locations
* Extracting production requirements
* Generating higher-level scene intelligence

The AI output is expected to follow a structured format rather than returning unrestricted natural-language responses.

This allows the application to process the results programmatically.

---

# 5. Data Normalization

AI-generated results are normalized before being presented to the application.

The normalization layer converts the extracted information into a consistent internal representation.

Conceptually:

```text
AI Output
    │
    ▼
Validation
    │
    ▼
Normalization
    │
    ▼
Structured Production Intelligence
```

This stage is important because downstream components should not depend directly on the exact wording or formatting produced by an AI model.

---

# 6. Production Intelligence Layer

The structured screenplay information is then organized into production-oriented intelligence.

The system can organize information around multiple dimensions:

```text
Screenplay
│
├── Scenes
│   ├── Scene number
│   ├── Location
│   ├── Time
│   └── Description
│
├── Characters
│   └── Scene appearances
│
├── Locations
│   └── Associated scenes
│
└── Production Information
    └── Scene-level requirements
```

This layer provides the bridge between screenplay analysis and the information required during production research.

---

# 7. Web Application

The processed information is exposed through the ScenePilot web application.

The interface allows users to inspect the results without having to work directly with the underlying extracted data.

The application separates:

* Document processing
* Analysis
* Data representation
* Presentation

This separation allows the analysis pipeline to evolve independently from the frontend interface.

---

# Architecture

At a high level, ScenePilot follows a layered architecture:

```text
┌─────────────────────────────────────────────┐
│                  Frontend                   │
│            Web UI / Dashboard               │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│               Application Layer             │
│        Routes / Request Handling            │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             Processing Layer                │
│                                             │
│  Document → Parser → AI → Normalization    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                Data Layer                   │
│       Structured screenplay information     │
└─────────────────────────────────────────────┘
```

---

# Technology Stack

## Backend

* **Python**
* **FastAPI**
* **Uvicorn**

FastAPI provides the HTTP application layer and API/request handling, while Uvicorn is used as the ASGI server during development and deployment.

## Frontend

* HTML
* CSS
* JavaScript
* Jinja2 templates

The frontend is responsible for presenting screenplay analysis and production intelligence generated by the backend.

## AI / NLP

The AI layer is used for semantic analysis of screenplay content and extraction of information that requires contextual understanding.

## Development Tools

* Git
* GitHub
* Python virtual environments

---

# Project Structure

The project follows a separation between application logic, templates, static assets, and screenplay-processing components.

```text
scenepilot/
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
│
├── templates/
│   ├── index.html
│   └── results.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
│
├── data/
│
├── uploads/
│
└── README.md
```

The exact structure may evolve as additional processing modules and persistence layers are introduced.

---

# Running Locally

## Prerequisites

* Python 3.x
* pip
* Git

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd scenepilot
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment on Windows:

```powershell
venv\Scripts\activate
```

On Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file containing the required configuration and API credentials.

Example:

```env
API_KEY=your_api_key
```

Credentials should not be committed to the repository.

---

## Start the Application

Run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload
```

The development server will be available at:

```text
http://127.0.0.1:8000
```

---

# Example Data Flow

For a screenplay containing:

```text
INT. APARTMENT - NIGHT

RAHUL enters the apartment.

He places a bag on the table.

ANITA enters from the bedroom.
```

ScenePilot can transform the information into structured data conceptually similar to:

```json
{
  "scene": 1,
  "location": "APARTMENT",
  "setting": "INT",
  "time": "NIGHT",
  "characters": [
    "RAHUL",
    "ANITA"
  ],
  "action": [
    "RAHUL enters the apartment.",
    "RAHUL places a bag on the table.",
    "ANITA enters from the bedroom."
  ]
}
```

The production intelligence layer can then use this structured representation to organize scene, character, and location information.

---

# Design Principles

ScenePilot is built around several engineering principles.

### Structured over free-form

Analysis results should be represented as structured data wherever possible.

### Separation of concerns

Document extraction, screenplay parsing, AI analysis, data normalization, and presentation should remain independently maintainable components.

### Deterministic processing where possible

Formatting-based information such as scene headings should be extracted using deterministic parsing before relying on AI interpretation.

### AI for semantic understanding

AI should be used where contextual interpretation provides value rather than replacing deterministic processing unnecessarily.

### Extensibility

The pipeline is designed so that additional production intelligence modules can be added without replacing the entire document-processing workflow.

---

# Current Scope

ScenePilot currently focuses on screenplay analysis and production intelligence generation.

The system is being developed incrementally, with the processing pipeline and dashboard forming the foundation for future production-planning capabilities.

Potential future extensions include:

* Automated shooting schedule generation
* Scene grouping by location
* Character appearance analysis
* Production-day optimization
* Advanced location intelligence
* Production report generation
* Export to production planning formats
* Project-level historical research
* Collaboration and multi-user workflows

These features are considered future development unless explicitly implemented in the current version.

---

# Development Status

ScenePilot is an actively developed project.

The current implementation focuses on establishing a reliable pipeline from:

```text
Screenplay
    ↓
Document Processing
    ↓
Screenplay Parsing
    ↓
AI Analysis
    ↓
Structured Data
    ↓
Production Intelligence
    ↓
Web Interface
```

The architecture is intended to provide a foundation for progressively adding more advanced production-planning functionality.

---

# License

License information will be added when the project license is finalized.

---


