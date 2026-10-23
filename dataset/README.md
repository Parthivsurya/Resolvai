# ResolvAI Campus Placement and Interview-Preparation Dataset

Supporting dataset for *ResolvAI: A Grounded Retrieval-Augmented Assistant for Campus
Placement and Interview Preparation* — Group 14, 23CSE471 Natural Language Processing,
Amrita School of Computing, Amrita Vishwa Vidyapeetham, Coimbatore.

English, campus-placement domain. Released so that the complete pipeline — intent
classification, retrieval and grounded generation — can be reproduced from one download.

## Components

| File | Rows | Schema | Unit of analysis |
|---|---|---|---|
| `placement_intents.csv` | 437 | `utterance, intent` | one labelled student utterance |
| `placement_questions.csv` | 67 | 10 columns (below) | one company interview question / topic |
| `placement_qa_eval.csv` | 50 | `question, ground_truth` | one grounded QA pair |
| `placement_abstention.csv` | 40 | `question, answerable, note` | one answerable / unanswerable query |
| `placement_kb/` | 24 docs | folder corpus | one source document |

The components differ in unit of analysis and are intended to be evaluated separately.

### 1. `placement_intents.csv` — intent corpus

Labelled student utterances over a 19-class placement intent taxonomy: `company_pyq`,
`aptitude_prep`, `coding_round`, `technical_interview`, `hr_interview`, `group_discussion`,
`resume_help`, `eligibility_criteria`, `placement_process`, `ctc_salary`, `company_info`,
`off_campus`, `internship`, `interview_experience`, `prep_roadmap`, `cutoff`, `greeting`,
`out_of_scope`, `talk_to_placement_officer`.

21–34 utterances per class. This component defines the taxonomy, supplies training and
evaluation data for the DistilBERT classifier, and encodes the routing contract between
intents and knowledge-base categories.

The taxonomy is deliberately fine-grained and classes overlap in vocabulary —
`eligibility_criteria` (*who may apply*), `cutoff` (*what score clears a round*) and
`placement_process` (*what the stages are*) all concern "requirements". This makes it a
single-domain fine-grained intent problem of the kind BANKING77 established as difficult.

### 2. `placement_questions.csv` — company interview-question bank

Structured interview questions extracted from the company archives in `placement_kb/pyq/`.
Columns:

`company`, `section`, `entry_type`, `title`, `difficulty`, `problem_statement`, `sample_io`,
`expected_solution`, `followups`, `source_file`

`entry_type` is one of `coding_question` (41 rows, each with a full problem statement,
sample I/O, expected solution with complexity, and interviewer follow-up), `scenario`
(system-design / low-level-design prompts), `concept`, or `topic` (viva and behavioural
entries). Companies covered: Amazon, Microsoft, Infosys, Wipro/Cognizant, TCS, Adobe, Meta.

Regenerate with `python3 -m scripts.export_dataset` from the repository root.

### 3. `placement_kb/` — retrieval corpus

Curated documents organised as `category/company/document`. **The folder path is the
metadata:** the first level is the document category and any level between the category and
the file is the company, so the corpus extends to a new company or category by adding a
folder — no code change.

```
placement_kb/
  pyq/tcs/tcs_nqt.md                   -> category=pyq,     company=tcs
  pyq/meta/meta_technical_5yr.docx     -> category=pyq,     company=meta
  hr/hr_round_faq.md                   -> category=hr,      company=none
  process/placement_process.md         -> category=process
  experience/interview_experience.md   -> category=experience
```

This is the retrieval corpus and the source of every citation the system emits. Supported
formats: `.md`, `.txt`, `.pdf`, `.docx`, `.csv`.

### 4. `placement_qa_eval.csv` — grounded evaluation set

Placement questions paired with a reference answer supported by the knowledge base. Drives
reference-free and reference-based scoring of the generation stage — faithfulness, answer
relevance, context precision and context recall. Every `ground_truth` is traceable to
indexed content. Questions are phrased independently of the corpus and are **not themselves
indexed**, so evaluation questions never appear in retrieval.

### 5. `placement_abstention.csv` — abstention evaluation set

A balanced mix of 20 answerable and 20 unanswerable questions, used to measure
correct-abstention and unnecessary-escalation rates as the confidence threshold is swept
(RQ1). The unanswerable half is deliberately weighted toward **in-domain but absent**
questions — a cut-off for a company not in the corpus, an institution-specific statistic —
because a plausible-sounding placement question that the corpus cannot answer is the case
where a system is most likely to fabricate. Fully out-of-domain questions are the easier
case and are included for contrast. The `note` column records why each is answerable or not.

## Release statistics

| Component | Unit | Count | Notes |
|---|---|---|---|
| Intent corpus | labelled utterance | 437 across 19 classes | 21–34 per class |
| Knowledge base | document | 24 in 5 categories | 10 company folders |
| Knowledge base | retrieval chunk | 166 | at 800/120 chunking |
| Vector index | embedding | 166 × 384 dimensions | `BAAI/bge-small-en-v1.5`, cosine, Chroma |
| Question bank | question / topic | 67 | 41 with full solution and complexity |
| Evaluation set | QA pair | 50 | held out of the retrieval corpus |
| Abstention set | query | 40 | 20 answerable / 20 unanswerable |

Chunk counts correspond to the released chunking configuration of 800 characters with 120
characters of overlap; a different configuration yields a different chunk count over the
same documents.

Categories `aptitude` and `coding` are defined by the routing contract but currently
unpopulated. The `company_profile` category holds per-company eligibility, round structure,
cutoff and CTC documents for 9 companies plus a cross-company comparison summary; those
figures are **representative sample data compiled for the prototype, not official company
notifications**, and each document states so. Because category and company are carried in the folder layout,
populating them is an additive change requiring no modification to the pipeline.

## Baseline result

Intent classification, DistilBERT (`distilbert-base-uncased`) fine-tuned for 20 epochs,
batch size 8, learning rate 3e-5, max sequence length 64, on a stratified 80/20 split:

| Metric | Value |
|---|---|
| Accuracy | 0.795 |
| Macro-F1 | 0.794 |

Measured on the held-out split produced by `backend.nlp.intent.split_dataset()`. Training
and evaluation share that one function deliberately: splitting independently with different
parameters overlaps the held-out set with the training set and inflates the result.

Per-class results confirm the expected confusion: `placement_process`, `eligibility_criteria`
and `cutoff` are the weakest classes, which is the vocabulary overlap the taxonomy design
anticipated. Retrieval, generation and abstention metrics are not yet reported.

## Reproducing

```bash
python3 -m scripts.export_dataset      # rebuild these CSVs from the corpus
python3 -m backend.ingest.build_index  # build Chroma + BM25 over placement_kb/
python3 -m backend.nlp.intent          # fine-tune the intent classifier
python3 -m backend.eval.intent_eval    # accuracy / macro-F1 / per-intent report
```

## Ethics and privacy

Documents are curated or synthesised placement material, not scraped personal data.
The ingestion pipeline masks emails, phone numbers and roll numbers with placeholder tokens
before indexing, and optional spaCy NER masking of person names is available for free-text
interview experiences. No student record, identifier or contact detail is included.

## Licence and citation

Released for academic and research use. Please cite the accompanying case study.

> P. K. B., A. Muhammed and R. G., "ResolvAI: A Grounded Retrieval-Augmented Assistant for
> Campus Placement and Interview Preparation," Amrita School of Computing, Amrita Vishwa
> Vidyapeetham, Coimbatore, 2026.
