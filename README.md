# 🔐 EvidenTrace — Explain Before You Alert

### Explainable Login Anomaly Detection and Investigation System

**CyberHack ENG-02 | Team EvidentX**

EvidenTrace is a cybersecurity application designed to identify suspicious login activities, validate login datasets, and provide understandable explanations behind generated security alerts.

Instead of simply notifying administrators about suspicious activities, EvidenTrace focuses on explaining **why an event is suspicious and what evidence supports the alert**, enabling more informed human investigation.

---

## 🚀 Project Overview

Traditional security monitoring systems can generate alerts without providing sufficient context for administrators to understand the underlying activity.

EvidenTrace addresses this challenge through:

- Automated login anomaly detection.
- Login dataset validation and normalization.
- Evidence-based alert explanations.
- Interactive alert investigation.
- Human-in-the-loop review management.
- Automated testing with edge-case coverage.

**Our core principle: Explain before you alert.**

---

## ✨ Key Features

### 1. Security Overview
- Dashboard displaying login activity and security alerts.
- Overview of suspicious activities.
- Summary of dataset information and detection results.

### 2. Alert Investigation
- Displays generated security alerts.
- Provides explanations for suspicious login patterns.
- Shows supporting evidence and verification steps.
- Helps administrators investigate alerts.

### 3. Login Explorer
- Explore uploaded login records.
- Inspect account, computer, IP address, timestamp, and login outcome.
- Examine individual login activities.

### 4. Rules & Lab Schedule
- Configure detection settings.
- Review suspicious activity detection rules.
- Manage lab access schedules.

### 5. Data Quality & QA
- Detect duplicate event IDs.
- Identify missing timestamps.
- Detect invalid timestamp formats.
- Identify unknown login outcomes.
- Validate IP addresses.
- Run automated test cases.

### 6. Alert Review Management

Administrators can assign review statuses to generated alerts:

| Status | Description |
|---|---|
| Open | Alert awaiting investigation |
| Under Review | Alert currently being investigated |
| Resolved | Investigation completed and case handled |
| False Positive | Alert determined to represent legitimate activity |

### 7. Multiple CSV Schema Support

EvidenTrace supports two input formats:

**Synthetic Schema**

`event_id, system_no, ip_address, roll_no, department, timestamp, login_result`

**Official Schema**

`event_id, timestamp, account, computer, event, department_case`

The application normalizes supported column structures into a common format before validation and detection.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and detection logic |
| Streamlit | Interactive web application |
| Pandas | Dataset processing and validation |
| SQLite | Local persistence for review statuses and rule settings |
| Pytest | Automated testing |
| Altair | Visualization dependency |

---

## 🏗️ Project Architecture

```text
EvidenTrace/
│
├── app.py
├── requirements.txt
├── README.md
│
├── evidentrace/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── validation.py
│   ├── detection.py
│   ├── evidence.py
│   ├── scheduling.py
│   └── review.py
│
├── sample_data/
│   ├── sample_synthetic.csv
│   └── sample_official.csv
│
└── tests/
    ├── __init__.py
    ├── test_detection.py
    ├── test_validation.py
    └── test_edge_cases.py
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `ingestion.py` | CSV loading, schema detection, and column normalization |
| `validation.py` | Data quality checks and valid record extraction |
| `detection.py` | Suspicious login pattern detection |
| `evidence.py` | Evidence and event timeline generation |
| `scheduling.py` | Lab schedule handling |
| `review.py` | Alert review status management |
| `app.py` | Streamlit application and dashboard |

---

## ⚙️ How It Works

```text
        CSV LOGIN DATA
               |
               v
       SCHEMA DETECTION
               |
               v
      DATA NORMALIZATION
               |
               v
       DATA VALIDATION
               |
               v
    VALID LOGIN RECORDS
               |
               v
    ANOMALY DETECTION
               |
               v
       ALERT GENERATION
               |
               v
      EVIDENCE EXPLANATION
               |
               v
      HUMAN INVESTIGATION
               |
               v
       ALERT CLASSIFICATION
```

The system processes supported login datasets, validates records, applies detection rules, generates alerts with supporting evidence, and allows administrators to review the results.

---

## 🧪 Automated Testing

EvidenTrace includes an automated testing suite covering detection, validation, and edge-case scenarios.

**Project testing results:**

- 39 automated tests passed.
- 23 edge cases included in the test suite.
- Test execution time in the demonstrated run: approximately 2.51 seconds.

### Run Tests

```bash
python -m pytest tests -v
```

To generate a test report:

```bash
python -m pytest tests -v --tb=short
```

---

## 💻 Installation and Setup

### Prerequisites

- Python 3.10 or later.
- Git.
- Visual Studio Code (recommended).

### 1. Clone the Repository

```bash
git clone https://github.com/Gokul-2808/Evidentrace.git
```

### 2. Navigate to the Project

```bash
cd Evidentrace
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Environment

**Windows PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python -m streamlit run app.py
```

The application will open in your browser, usually at:

```text
http://localhost:8501
```

---

## 🌐 Deployment

EvidenTrace is deployed using **Streamlit Community Cloud**.

Deployment process:

1. Push the project repository to GitHub.
2. Connect GitHub to Streamlit Community Cloud.
3. Select the Evidentrace repository.
4. Choose the `main` branch.
5. Set the main file path to `app.py`.
6. Deploy the application.

**Deployment platform:** [Streamlit Community Cloud](https://share.streamlit.io/)

---

## 🔒 Data and Security Considerations

- Use synthetic or anonymized login records for demonstrations.
- Avoid uploading confidential student information or real authentication logs to public repositories.
- Validate uploaded datasets before processing.
- Review suspicious alerts before taking security action.
- SQLite data stored on cloud hosting may not persist across application restarts or redeployments.

---

## 🎯 Project Objectives

1. Develop an explainable login anomaly detection system.
2. Improve visibility into suspicious login activities.
3. Identify data-quality problems before analysis.
4. Provide evidence-based explanations for generated alerts.
5. Support human investigation and alert classification.
6. Build a modular, testable, and deployable cybersecurity application.

---

## 👥 Team

**Team Name:** EvidentX

**Project:** EvidenTrace — Explain Before You Alert

**Event:** CyberHack ENG-02

---

## 🔮 Future Enhancements

- Advanced anomaly detection using machine learning.
- Real-time login event ingestion.
- Improved alert prioritization.
- Role-based access control.
- Persistent cloud database integration.
- Advanced investigation and reporting capabilities.

---

## 💡 Our Vision

We believe cybersecurity alerts should be more than warnings.

They should provide context, evidence, and explanations that help people make better security decisions.

**EvidenTrace — Explain Before You Alert.**

---

⭐ If you find this project interesting, consider starring the repository!
