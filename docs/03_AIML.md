# AI & Machine Learning Specification

## Digital Ecosystem Intelligence Platform --- MVP

**Founders:** Unnati Kadam and Aryan Chavan\
**Document owner:** AI/ML workstream\
**Status:** Build blueprint for MVP\
**Version:** 1.0

------------------------------------------------------------------------

## 1. AI/ML mission

The AI/ML layer converts permitted, timestamped, source-attributed
signals into useful, explainable outputs:

1.  Identify topics and themes in collected content or campaign data.
2.  Detect topics whose activity is increasing relative to a baseline.
3.  Group related topics into interpretable interest clusters.
4.  Estimate short-term trend direction only when sufficient history
    exists.
5.  Rank potential opportunities using transparent evidence.
6.  Explain why an insight was produced and where it may be wrong.

The MVP should be useful before advanced models exist. Begin with robust
descriptive analytics and simple statistical baselines. Add complexity
only when it improves measured performance.

------------------------------------------------------------------------

## 2. First customer problem

**Initial customer:** a small D2C brand or marketing agency.

**Question:** "Which emerging themes in my category deserve attention,
what evidence supports them, and what campaign/content experiment should
I test?"

Initial vertical recommendation: choose one category such as sustainable
fashion/workwear, personal care or fitness. The sustainable workwear
example in this document is illustrative, not a claim about a live
market trend.

### MVP output

For a selected topic and date window: - activity volume over time. -
change versus previous comparable period. - trend momentum score. -
source coverage and freshness. - related terms/topics. - interest
cluster summary. - evidence examples where display rights permit. -
opportunity hypothesis and recommended experiment. -
confidence/limitations.

------------------------------------------------------------------------

## 3. Data and ML boundaries

### What the system can infer

-   Topic frequency and co-occurrence in permitted records.
-   Changes in aggregate activity over time.
-   Similarity between text records.
-   Broad interest clusters represented in the available dataset.
-   Historical campaign metric patterns from customer-authorised
    exports.

### What it must not claim

-   It cannot observe all activity on Instagram, LinkedIn or the
    internet.
-   A rising mention count does not prove rising purchases.
-   A trend score is not automatically a probability of success.
-   Topic clusters are not verified demographic or psychological
    identities.
-   Correlation between social signals and campaign outcomes is not
    causal proof.
-   Creator reach or audience quality cannot be independently verified
    unless reliable authorised data is available.

------------------------------------------------------------------------

## 4. ML pipeline

``` mermaid
flowchart TD
  A[Permitted source records] --> B[Schema and quality checks]
  B --> C[Language detection and normalization]
  C --> D[Deduplication]
  D --> E[Text preprocessing]
  E --> F[Topic extraction and embeddings]
  F --> G[Daily topic aggregation]
  G --> H[Trend features]
  H --> I[Baseline trend scoring]
  I --> J[Optional forecasting]
  G --> K[Topic clustering]
  I --> L[Opportunity ranking]
  J --> L
  K --> L
  L --> M[Explainable insight API]
  M --> N[Dashboard and reports]
```

### Stage 0 --- Data quality

Before modelling, validate: - timestamp exists and is parseable. -
source identifier and source type are known. - text field is within
permitted length. - duplicate IDs/checksums are handled. - language is
supported or marked unknown. - source permissions and retention metadata
exist. - timestamps are normalized to UTC while preserving source
timezone where needed.

Do not train on records with unclear provenance or rights.

### Stage 1 --- Text normalization

-   Unicode normalization.
-   whitespace cleanup.
-   URL and tracking parameter handling.
-   language detection.
-   spam/boilerplate filtering with conservative rules.
-   tokenization appropriate to language.
-   optional lemmatization for supported languages.

Retain a link to the original source record where retention and display
permissions allow. Store transformed text separately from raw source
payload.

### Stage 2 --- Topic extraction

MVP approaches: 1. TF-IDF + keyphrase extraction for transparent
baseline. 2. Sentence-transformer embeddings for semantic similarity. 3.
HDBSCAN or K-Means for grouping embeddings, with human review. 4.
Human-readable labels generated from representative terms, then
reviewed.

Start with a small, evaluated embedding model. Do not assume a large
language model is necessary for the core ranking.

### Stage 3 --- Trend detection

Aggregate records by topic and day/week.

For topic (k), let (V\_{k,t}) be the count or normalized signal volume
in time bucket (t).

Basic period change: \[ `\text{change}`{=tex}*{k} =
`\frac{V_{\text{current}}-V_{\text{previous}}}`{=tex}
{`\max`{=tex}(V*{`\text{previous}`{=tex}}, `\epsilon`{=tex})} \]

Use a small smoothing constant only for numerical stability; label the
handling of zero baselines.

A simple MVP momentum score can combine: - normalized recent growth. -
persistence across multiple time buckets. - source diversity. - minimum
sample-size factor. - freshness.

Example: \[ S_k = 100(0.40G_k + 0.25P_k + 0.20D_k + 0.15Q_k) \] where: -
(G): capped and normalized growth. - (P): persistence (how many recent
periods show positive growth). - (D): source diversity/coverage. - (Q):
data-quality and sample-size factor.

These weights are initial product heuristics, not learned truths.
Version them, document them and validate them against analyst judgements
and future outcomes.

### Stage 4 --- Forecasting

Only forecast after enough regular history exists. Compare: - seasonal
naive baseline. - moving average / exponential smoothing. - Prophet or
StatsForecast where justified. - tree-based regression with lagged
features only if there is enough data.

Evaluation: - rolling-origin time-series cross-validation. - MAE and
WAPE; use MAPE only when values are nonzero and meaningful. - compare
against naive baseline. - report prediction intervals where model
supports them. - monitor performance by topic and source.

If history is short or unstable, show "insufficient history for
forecast" instead of inventing a prediction.

### Stage 5 --- Audience/interest clustering

MVP clusters are based on permitted topic/content embeddings, not
inferred personal identity.

Workflow: 1. Build embeddings for eligible records. 2. Normalize
vectors. 3. Reduce dimensions for exploration if needed (UMAP). 4.
Cluster (HDBSCAN or K-Means). 5. Extract representative terms and
records. 6. Measure cluster size and stability. 7. Review labels and
merge/split noisy clusters.

Evaluation: - silhouette score where appropriate. - cluster stability
under resampling. - human review of coherence. - minimum cluster size
and suppression rules. - avoid displaying clusters that are too small to
protect privacy.

### Stage 6 --- Opportunity ranking

Opportunity score is a decision-support ranking, not a guaranteed
commercial outcome.

Potential components: - trend momentum. - source diversity. -
persistence. - relevance to the workspace's selected category. - fit
with uploaded campaign outcomes, if available. - evidence quality. -
counter-signals or saturation indicators.

Show a breakdown so users understand the score. Never present a single
unexplained "AI opportunity probability".

------------------------------------------------------------------------

## 5. Model inventory and priority

  -----------------------------------------------------------------------------
  Capability        MVP priority      Baseline               Advanced later
  ----------------- ----------------- ---------------------- ------------------
  Topic/keyphrase   Must              TF-IDF/keyBERT-style   Domain-adapted NLP
  extraction                          extraction             

  Semantic grouping Should            Sentence embeddings +  Graph/community
                                      clustering             detection

  Trend ranking     Must              Statistical heuristic  Learned ranking

  Forecasting       Conditional       Seasonal naive /       Global time-series
                                      moving average         models

  Audience interest Should            Embedding clustering   Dynamic topic
  clusters                                                   graph

  Opportunity       Should            Rules + weighted score Learning-to-rank
  recommendation                                             

  Creator-brand     Later             Structured filters     Graph recommender
  matching                                                   

  Campaign outcome  Later             Historical baseline    Supervised model
  prediction                                                 after enough
                                                             labels

  Graph ML          Research phase    Co-occurrence graph    GNNs if justified
                                      analytics              
  -----------------------------------------------------------------------------

Do not implement all rows before MVP. The core product can launch with
trend ranking, transparent evidence and campaign analytics.

------------------------------------------------------------------------

## 6. Feature engineering

### Topic-time features

-   `mention_count`
-   `unique_source_count`
-   `unique_record_count`
-   `rolling_mean_7d`
-   `rolling_mean_28d`
-   `growth_rate_7d`
-   `growth_rate_28d`
-   `positive_period_ratio`
-   `volatility`
-   `source_entropy`
-   `days_since_last_observation`

### Text features

-   TF-IDF vector.
-   sentence embedding.
-   keyphrase set.
-   language code.
-   duplicate similarity.
-   content length bucket.

### Campaign features (only from authorised exports)

-   impressions, clicks, spend, conversions, attributed revenue.
-   CTR, CPC, CPM, CPA, ROAS.
-   campaign/channel/creative category.
-   date and currency.
-   missingness and data-quality flags.

Do not include direct personal identifiers in model features. Do not
join campaign records to named social users.

------------------------------------------------------------------------

## 7. Training and evaluation protocol

### Data splits

-   Use time-based splits for trend forecasting.
-   Avoid random train/test splits for time-dependent data.
-   Group duplicate or near-duplicate content so copies cannot leak
    across splits.
-   Keep a final untouched test window.
-   Track source and topic distribution across splits.

### Baselines

Every advanced model must beat a simple baseline on a relevant metric: -
forecasting must beat seasonal naive. - classifier must beat majority
class and a simple linear model. - recommender must beat popularity or
rules baseline. - clustering must improve human-rated
coherence/stability, not just a metric.

### Human evaluation

Create an analyst-labelled evaluation set: - 100--300 topic/time
examples initially. - labels: rising, stable, declining,
noisy/insufficient evidence. - two reviewers for a subset. - record
disagreements and revise rubric.

For opportunity briefs, reviewers rate: - evidence relevance. -
actionability. - clarity. - unsupported claims. - usefulness to a real
marketing decision.

### Model registry

Store: - model name/version. - training dataset version. - feature
schema version. - training window. - hyperparameters. - code commit. -
evaluation metrics. - known limitations. - deployment date.

Never overwrite a deployed model artifact without a new version.

------------------------------------------------------------------------

## 8. Explainability and user-facing confidence

Every trend card should explain: - what changed. - comparison period. -
number of records. - number/types of sources. - persistence. - last
update. - why confidence is low/medium/high.

Confidence should be based on explicit factors such as sample size,
missingness, source coverage and stability. It is not the same as model
probability.

Example explanation: \> "This topic is ranked as rising because its
normalized activity increased in three consecutive weekly buckets,
appeared in two permitted source categories and has enough observations
for the current threshold. Evidence is still limited to the connected
sources and does not prove purchase intent."

------------------------------------------------------------------------

## 9. Example: sustainable workwear

Illustrative workflow: 1. Import licensed/public sample text about
clothing and sustainability, plus an authorised brand campaign export.
2. Normalize dates and text; record source provenance. 3. Extract
phrases such as "capsule wardrobe", "office basics", "recycled fabric".
4. Embed text and group semantically related records. 5. Aggregate topic
counts weekly. 6. Compare recent activity with previous periods. 7. Rank
candidate rising topics. 8. Cluster related interests, such as
"professional wardrobe", "fabric transparency" and "affordable basics".
9. Compare topic timing with the brand's campaign results only at
aggregate category/date level. 10. Generate an opportunity hypothesis:
test sustainable office basics with content explaining fabric,
durability and price. 11. Display evidence, limitations and an
experiment plan. 12. After the brand runs the experiment, upload results
and compare actual performance.

This is a hypothesis-generation workflow, not proof that the market will
buy the product.

------------------------------------------------------------------------

## 10. Implementation pseudocode

``` python
def build_daily_topic_signals(records, embedder, topic_model):
    eligible = [
        r for r in records
        if r.permission_status == "approved"
        and r.timestamp is not None
        and r.text
    ]

    normalized = [normalize_text(r.text) for r in eligible]
    vectors = embedder.encode(normalized, normalize_embeddings=True)
    labels = topic_model.fit_predict(vectors)

    rows = []
    for record, label in zip(eligible, labels):
        if label == -1:  # noise/unassigned cluster
            continue
        rows.append({
            "topic_cluster": int(label),
            "date": record.timestamp.date(),
            "source_type": record.source_type,
            "record_id": record.id,
        })

    return aggregate_counts(rows)
```

Production code must use stable topic IDs across runs; raw cluster
integer labels are not stable identities. Align clusters to prior
versions using centroid similarity and human review.

------------------------------------------------------------------------

## 11. Serving and refresh strategy

-   Run daily batch processing for MVP.
-   Store derived topic/day aggregates.
-   Precompute trend summaries for fast dashboard reads.
-   Store embeddings separately from transactional rows when volume
    grows.
-   Cache common trend queries.
-   Record source freshness and model run timestamp.
-   Recompute only affected date ranges where practical.

Do not call embedding models on every page load.

------------------------------------------------------------------------

## 12. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Sparse or biased source data        Show coverage and sample size;
                                      support multiple permitted sources

  Platform API access changes         Keep source adapters independent;
                                      CSV/demo fallback

  Trend spikes caused by spam         Deduplication, anomaly filters,
                                      source-quality factor

  Topic clusters are hard to          Human review and editable labels
  interpret                           

  Forecasts are unreliable            Baseline comparison and abstain
                                      when history is insufficient

  Correlation mistaken for causation  Use "associated with" language;
                                      recommend experiments

  Sensitive inference                 No sensitive attribute prediction;
                                      aggregate and suppress small groups

  Model drift                         Monitor input distributions and
                                      rolling evaluation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 13. AI/ML milestones

  Sprint   Deliverable
  -------- ----------------------------------------------------------------
  1        Define target labels, source eligibility and evaluation plan
  2        Data quality, normalization, deduplication
  3        TF-IDF/keyphrase baseline and daily aggregation
  4        Embeddings and semantic grouping
  5        Trend score, persistence and confidence logic
  6        Interest clusters and analyst review
  7        Forecast experiment only if sufficient history; model registry
  8        API integration, explanation text, evaluation and monitoring

------------------------------------------------------------------------

## 14. MVP acceptance criteria

-   Trend scores are reproducible for a fixed dataset and code version.
-   Every result links to source provenance and a processing run.
-   Trend ranking has a documented baseline and transparent components.
-   Forecasting is hidden/abstained when data is insufficient.
-   Cluster labels can be reviewed and edited.
-   No sensitive personal attributes are inferred.
-   Evaluation uses time-aware splits and baseline comparisons.
-   Opportunity briefs identify evidence separately from hypotheses.
-   Model versions and metrics are stored.
-   At least one real user can explain why a displayed trend was ranked.

------------------------------------------------------------------------

## 15. Later research roadmap

After the MVP has repeat usage and labelled outcomes: 1. Knowledge graph
connecting topics, products, brands, creators and industries. 2.
Graph-based community and co-occurrence analysis. 3. Learning-to-rank
for opportunity recommendations. 4. Creator-brand fit models using
authorised aggregate creator metrics. 5. Campaign response modelling
with sufficient historical data and clear attribution. 6. Multilingual
NLP for Indian languages after a separate evaluation set is built. 7.
Drift-aware and uncertainty-calibrated forecasting.

Advanced graph neural networks are not an MVP requirement. Begin with
graph analytics and prove that relationships improve decisions before
training a GNN.
