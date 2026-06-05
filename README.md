# 🩺 Predictive InsurTech Cost Estimation Platform

An enterprise-grade health insurance premium prediction and risk analytics platform. The system leverages an advanced **Gradient Boosting Machine Learning pipeline** ($R^2: 0.89$) for real-time inference, backed by a persistent relational **Microsoft SQL Server** infrastructure, and delivered through a premium, responsive dark-themed analytical interface.

---

## 🎯 System Architecture

The platform bridges the gap between traditional reactive underwriting and proactive actuarial risk mitigation. By capturing individual biometric data and high-impact lifestyle coefficients, the system executes real-time predictive modeling, registers transaction audits to a secure relational database, and dynamically computes multi-scenario lifestyle optimization deltas ("What-If" analytics) to encourage preventive healthcare pathways.

---

## 🛠️ Technology Stack & Infrastructure

- **Interactive Interface Layer:** Streamlit Framework (Advanced Session State & DOM Management)
- **Predictive Analytics Engine:** Scikit-Learn (Gradient Boosting Regressor Pipeline)
- **Data Persistence Layer:** Microsoft SQL Server (MS SQL) via Native OS `pyodbc` Connectors
- **Document Assembly Subsystem:** ReportLab PDF Generation Library (Dynamic Grid Coordinates)
- **Aesthetic Core:** Embedded CSS Overrides (Neo-Brutalism Minimalist Dark Theme)

---

## 💾 Relational Database Schema Design

The application features an automated database initializer that verifies infrastructure integrity at runtime. If the deployment environment lacks the pre-configured relational schema, the engine autonomously creates the targeted catalog and initializes the following audited logging table:

### `dbo.predictions` Table Specification

| Column Name | Data Type | Constraint | Engineering Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `IDENTITY(1,1) PRIMARY KEY` | Auto-incremented unique relational surrogate key. |
| `age` | `INT` | `NOT NULL` | Policyholder age baseline constraint ($18 \le \text{Age} \le 100$). |
| `height` | `INT` | `NOT NULL` | Physical metric evaluated in centimeters for BMI normalization. |
| `weight` | `INT` | `NOT NULL` | Physical mass evaluated in kilograms for BMI normalization. |
| `bmi` | `FLOAT` | `NOT NULL` | Mathematically calculated Body Mass Index ($\text{BMI} = \frac{\text{weight}}{\text{height}_m^2}$). |
| `gender` | `VARCHAR(10)` | `NOT NULL` | Categorical demographic feature vector (`Male`, `Female`). |
| `children` | `INT` | `NOT NULL` | Quantitative dependant index ($0 \le \text{Children} \le 5$). |
| `smoker` | `VARCHAR(5)` | `NOT NULL` | High-impact categorical risk coefficient (`Yes`, `No`). |
| `region` | `VARCHAR(20)` | `NOT NULL` | Actuarial geographical zone sector classification. |
| `estimated_cost` | `FLOAT` | `NOT NULL` | Continuous target variable representing the final annual premium ($). |
| `timestamp` | `DATETIME` | `DEFAULT GETDATE()` | Automated system-level transaction audit log timestamp. |

---

## 🔮 Core Subsystem Deployments

### 1. Machine Learning Inference Pipeline
The regression matrix utilizes pre-trained Gradient Boosting Decision Trees. During runtime inference, the raw numeric inputs (`Age`, `BMI`) pass through an explicit serialization layer (`scaler.pkl`) to prevent any operational data leakage before being evaluated against the final serialized model parameters (`model.pkl`).

### 2. Proactive "What-If" Financial Simulation Engine
To deliver algorithmic business value, the system embeds an interactive multi-scenario simulator. If high-risk thresholds are detected (tobacco dependency or $\text{BMI} > 24.9$), the engine triggers a secondary parallel inference cycle with optimized baseline inputs ($\text{Smoker} = \text{No}$, $\text{BMI} = 22.0$). It instantly projects the theoretical premium drop, presenting the user with exact annual financial savings.

### 3. InMemory PDF Document Generation
The document assembly layer directly manipulates binary object arrays (`io.BytesIO`) to build official insurance quote reports on the fly. It programmatically maps data tables, enforces typography hierarchies (`Helvetica`), and outputs formal risk disclosure documentation without requiring local server disk storage.

---

## 🚀 Installation & Local Environment Setup

### System Prerequisites
- **Python Runtime:** Python 3.9 or higher
- **Database Server:** Microsoft SQL Server (Instance configured with Windows Authentication)
- **System Drivers:** Microsoft ODBC Driver 17 for SQL Server

### Deployment Pipeline
```bash
# 1. Clone repository to local environment
git clone [https://github.com/amineacar/Insurance-Cost-Estimate.git](https://github.com/amineacar/Insurance-Cost-Estimate.git)
cd Insurance-Cost-Estimate

# 2. Configure dedicated isolated virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows command: venv\Scripts\activate

# 3. Install required upstream packages
pip install -r requirements.txt

Dependency Validation
Ensure the root directory contains the following serialized artifact binaries before execution:

model.pkl (Trained model weights)

scaler.pkl (Standardization mapping vectors)

Execution

streamlit run app.py

Note: Upon execution, the logging engine will securely test the localhost SQL connection, compile the structural schema logs, and map all structural assets without requiring external configuration scripts.


Engineering & Contributions
Emre Erden - Relational Database Architecture, Document Assembly Subsystem & Business Logic Integrations

Amine Acar - UI/UX Interface Engineering, Machine Learning Pipeline Integration & System Localization

Disclaimer: This software is an InsurTech proof-of-concept driven by statistical data grid models. The predictions generated do not constitute a legally binding insurance underwriting contract.
