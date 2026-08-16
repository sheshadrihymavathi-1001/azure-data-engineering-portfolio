# 🚀 Day 1/90 — GenAI + Azure Data Engineering

## My 90-Day Learning Journey

I'm starting a **90-day journey to learn GenAI-based Azure Data Engineering**.

The objective isn't just to learn AI tools or memorize definitions.

My approach is:

> **Business problem → limitation → solution → new problem → next solution**

I want to understand **why each technology exists**, how the pieces connect, and how GenAI can be built on top of a strong Data Engineering foundation.

---

# 🎯 Day 1 Objective

Today I focused on understanding:

* AI vs Machine Learning vs Deep Learning vs Generative AI
* Large Language Models (LLMs)
* How GenAI connects with Data Engineering
* Why LLMs don't automatically know private enterprise data
* RAG
* Tool Calling
* Agents
* The role of a Data Engineer in enterprise GenAI

---

# 1. AI → ML → Deep Learning → GenAI

I started by understanding the relationship between these concepts.

```text
Artificial Intelligence
        │
        └── Machine Learning
                │
                └── Deep Learning
                        │
                        └── Foundation Models
                                │
                                └── Generative AI
```

### Artificial Intelligence

The broader concept of machines performing tasks that normally require intelligence.

### Machine Learning

Machines learn patterns from data and use those patterns to make predictions or decisions.

Example:

```text
Historical transactions
        ↓
      ML Model
        ↓
Fraud probability = 87%
```

### Deep Learning

Uses neural networks to learn complex patterns from large amounts of data.

### Generative AI

Instead of only predicting or classifying, the system can **generate new content**.

Examples:

* Text
* SQL
* Code
* Summaries
* Explanations
* JSON
* Images
* Audio

---

# 2. What is an LLM?

An **LLM (Large Language Model)** is a model capable of understanding and generating language-based content.

For example:

```text
Input
  ↓
LLM
  ↓
Output
```

Input:

> Explain a left join.

Output:

> An explanation of how a left join works.

Another example:

```text
"Write SQL to find the top 10 customers"
              ↓
             LLM
              ↓
             SQL
```

An important distinction I learned:

> **An LLM is not the same thing as ChatGPT.**

An LLM can be used inside many different applications, including enterprise AI applications.

---

# 3. The first major problem — Private enterprise data

Now comes the important question:

> If an LLM is so powerful, why can't I simply ask it about my company's data?

For example:

> "What was our company's revenue last month?"

The LLM may understand what **revenue** means.

But it doesn't automatically know my company's actual revenue.

Why?

Because enterprise information may exist inside:

* Sales databases
* Customer databases
* Databricks
* Internal documents
* APIs
* Other private systems

So I learned:

> **General knowledge is not the same as private enterprise data.**

---

# 4. Problem → RAG

Suppose an organization has **500,000 PDF documents** containing:

* Policies
* Procedures
* Technical documentation
* Business information
* Internal knowledge

A user asks:

> "What is our international travel policy?"

The answer exists somewhere in those documents.

We need to find the relevant information and provide it to the LLM.

This leads to:

# RAG — Retrieval-Augmented Generation

The basic mental model:

```text
User Question
      ↓
Retrieve Relevant Information
      ↓
Provide Context to LLM
      ↓
LLM Generates Answer
```

My Day 1 understanding:

> **RAG allows an LLM application to retrieve relevant enterprise knowledge and use that information when generating an answer.**

I haven't yet gone deep into embeddings, chunking or vector search. Those will come later in this 90-day journey.

---

# 5. Problem → Tool Calling

Now consider:

> "What was our APAC revenue last month?"

The answer may exist in a structured database.

For example:

```text
Sales Database
      ↓
Revenue Table
      ↓
SQL Query
      ↓
Result
```

The AI needs to interact with the database.

This leads to:

# Tool Calling

Basic mental model:

```text
User Question
      ↓
LLM
      ↓
Decides a tool is required
      ↓
SQL / Database Tool
      ↓
Database
      ↓
Result
      ↓
LLM
      ↓
Answer
```

My current understanding:

> **Tool calling allows an LLM to interact with external systems or capabilities.**

For example:

* SQL/database
* APIs
* Search
* Python functions
* Business applications

---

# 6. Problem → Agents

Now consider a more complex question:

> "Why did our APAC revenue decrease last month? Also check whether there were any policy or business changes that might explain it."

This may require multiple actions:

```text
1. Check APAC revenue
        ↓
2. Compare with previous month
        ↓
3. Analyze the decline
        ↓
4. Search business documents
        ↓
5. Check policy/business changes
        ↓
6. Combine the information
        ↓
7. Generate an explanation
```

This is where an **Agent** becomes useful.

An agent can potentially orchestrate multiple tools and actions.

```text
                    Agent
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
      SQL           Search         API
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                   Results
                      ↓
                   Analysis
                      ↓
                    Answer
```

My Day 1 understanding:

> **An agent is useful when a task requires multiple actions/tools and the system needs to orchestrate those actions to accomplish the task.**

---

# 7. RAG vs Tool Calling vs Agents

This is the mental model I currently have:

| Requirement                                    | Concept      |
| ---------------------------------------------- | ------------ |
| Retrieve relevant enterprise knowledge         | RAG          |
| Search internal documents                      | RAG          |
| Interact with a database                       | Tool Calling |
| Execute SQL                                    | Tool Calling |
| Call an API                                    | Tool Calling |
| Perform multiple actions using different tools | Agent        |
| Orchestrate RAG + SQL + APIs                   | Agent        |

The important point is that these aren't necessarily competing technologies.

An agent can use **RAG and tools together**.

---

# 8. Where does Data Engineering fit?

This is the connection that matters most to me.

My existing Data Engineering world looks like:

```text
Source Systems
      ↓
Ingestion
      ↓
ADLS
      ↓
Databricks
      ↓
Spark
      ↓
Delta
      ↓
Transformations
      ↓
Analytics
```

GenAI doesn't replace this.

Instead, GenAI can sit on top of the data platform.

```text
                    AI Application
                           ↓
                         Agent
                     /          \
                    ↓            ↓
                  RAG         SQL Tool
                   ↓              ↓
              Documents       Databricks
                                  ↓
                                Delta
                                  ↓
                           Enterprise Data
```

---

# 9. Data Engineering becomes the foundation

A GenAI application can only be as reliable as the data and systems supporting it.

Important Data Engineering responsibilities include:

### Data Ingestion

Bring data from different enterprise systems into the platform.

### Data Transformation

Convert raw data into clean and usable data.

### Data Quality

Ensure that the underlying information is accurate.

### Data Freshness

Ensure that AI applications aren't answering from stale data.

### Data Governance

Ensure users can access only the information they are authorized to access.

### AI-ready Data

Prepare enterprise data so that AI applications can retrieve and use it effectively.

This gave me one of my biggest Day 1 takeaways:

> **Good GenAI depends on good data and good engineering.**

---

# 10. Day 1 Mental Model

This is the architecture I have in my head after Day 1:

```text
                         USER
                           │
                           ▼
                    AI APPLICATION
                           │
                           ▼
                         LLM
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
                 RAG              Tools
                  │                 │
                  ▼                 ▼
             Documents        Databases / APIs
                                    │
                                    ▼
                               Databricks
                                    │
                                    ▼
                              Enterprise Data

                           ↑
                           │
                         Agent
                orchestrates multiple
                   actions / tools
```

And underneath everything:

```text
        DATA ENGINEERING FOUNDATION

    Ingestion
       ↓
    Transformation
       ↓
    Data Quality
       ↓
    Data Freshness
       ↓
    Governance
       ↓
    Reliable Enterprise Data
```

---

# 🧠 Key Takeaways

### 1.

> **An LLM doesn't automatically know private enterprise data.**

### 2.

> **RAG retrieves relevant enterprise knowledge for the LLM.**

### 3.

> **Tool calling allows the LLM to interact with external systems.**

### 4.

> **Agents can orchestrate multiple tools/actions for multi-step tasks.**

### 5.

> **Data Engineering provides the foundation that enterprise GenAI depends on.**

---

# 🔍 My Day 1 Learning Approach

Instead of memorizing:

> "RAG = Retrieval-Augmented Generation"

I tried to understand:

```text
LLM doesn't know private data
        ↓
Need enterprise information
        ↓
Retrieve relevant information
        ↓
Give it to LLM
        ↓
RAG
```

Similarly:

```text
LLM needs database information
        ↓
Database requires an operation
        ↓
Expose database capability as a tool
        ↓
Tool Calling
```

And:

```text
Task requires multiple actions
        ↓
Multiple tools are needed
        ↓
Need orchestration
        ↓
Agent
```

This problem-solving approach is how I plan to continue the remaining 89 days.

---

# 🚀 What's Next?

## Day 2 — How Does an LLM Actually Work?

Next, I'll explore:

* Tokens
* Tokenization
* Token IDs
* Context window
* Embeddings
* Transformers
* Attention
* Parameters
* Inference

The goal isn't to become an AI researcher.

The goal is to understand **what is happening inside an LLM well enough to design and engineer enterprise GenAI systems.**

---

# 📚 90-Day Journey

| Day | Topic                | Status      |
| --- | -------------------- | ----------- |
| 01  | GenAI Foundations    | ✅ Completed |
| 02  | How LLMs Work        | 🔜 Next     |
| 03  | Tokens & Context     | ⏳           |
| 04  | Model Behaviour      | ⏳           |
| 05  | Structured Outputs   | ⏳           |
| ... | ...                  | ⏳           |
| 90  | Capstone + Interview | ⏳           |

---

**Day 1/90 — Complete. 🚀**

> *Learning GenAI not by memorizing tools, but by understanding the problems that led to them.*

#GenAI #GenerativeAI #Azure #AzureDataEngineering #DataEngineering #Databricks #LLM #RAG #AI #LearningJourney
