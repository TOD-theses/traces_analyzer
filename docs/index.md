# Traces analyzer

The analysis is currently done in two steps:

1. Parse instructions from traces (see [Parsing](./parsing.md))
2. Run analyzers on instructions (see [Metadata Extraction](./metadata_extraction.md))

In the future, the second step will likely be renamed to "feature extraction" and a third step will process these "features" to assign labels and other metadata to contracts.
