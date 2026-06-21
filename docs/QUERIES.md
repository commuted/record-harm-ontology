# Example SPARQL Queries

This document provides example SPARQL queries for common use cases with the Record Harm Ontology.

## Setup

```python
from rdflib import Graph

g = Graph()
g.parse("ontology/record-harm-ontology.ttl", format="turtle")
g.parse("examples/example-harm-events.ttl", format="turtle")
```

## Basic Queries

### List All Prime Harms

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:PrimeHarm ;
          rdfs:label ?label .
}
ORDER BY ?label
```

### List All Composite Harms with Dependencies

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?composite ?label ?dependency ?depLabel WHERE {
    ?composite a ex:CompositeHarm ;
               rdfs:label ?label ;
               ex:buildsUpon ?dependency .
    ?dependency rdfs:label ?depLabel .
}
ORDER BY ?label ?depLabel
```

### Find Harms Targeting Specific Aspect

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?harm ?label ?definition WHERE {
    ?harm ex:targetsAspect ex:Authenticity ;
          rdfs:label ?label ;
          skos:definition ?definition .
}
```

## Dependency Analysis

### Find All Transitive Dependencies

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?composite ?label ?prime ?primeLabel WHERE {
    ?composite a ex:CompositeHarm ;
               rdfs:label ?label ;
               ex:buildsUpon+ ?prime .
    ?prime a ex:PrimeHarm ;
           rdfs:label ?primeLabel .
}
ORDER BY ?label ?primeLabel
```

### Find Harms That Build Upon Omission

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm ex:buildsUpon ex:Omission ;
          rdfs:label ?label .
}
```

### Count Underlying Prime Harms

Counts the distinct prime harms in each composite's transitive closure (how many
primes it ultimately rests on) — not path depth / longest chain, which would need
a recursive longest-path query.

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label (COUNT(DISTINCT ?prime) as ?primeCount) WHERE {
    ?harm a ex:CompositeHarm ;
          rdfs:label ?label ;
          ex:buildsUpon+ ?prime .
    ?prime a ex:PrimeHarm .
}
GROUP BY ?harm ?label
ORDER BY DESC(?primeCount)
```

## Event Queries

### List All Harm Events

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc: <http://purl.org/dc/terms/>

SELECT ?event ?label ?type ?date ?severity WHERE {
    ?event a ex:HarmEvent ;
           rdfs:label ?label ;
           ex:ofType ?harmType ;
           dc:date ?date .
    ?harmType rdfs:label ?type .
    OPTIONAL { ?event ex:severity ?severity }
}
ORDER BY DESC(?date)
```

### Find High-Severity Events

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?label ?severity ?record WHERE {
    ?event a ex:HarmEvent ;
           rdfs:label ?label ;
           ex:severity ?severity ;
           ex:harms ?record .
    FILTER(?severity >= 8)
}
ORDER BY DESC(?severity)
```

### Events by Perpetrator

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?perpetrator ?perpLabel (COUNT(?event) as ?eventCount) WHERE {
    ?event a ex:HarmEvent ;
           ex:perpetrator ?perpetrator .
    ?perpetrator rdfs:label ?perpLabel .
}
GROUP BY ?perpetrator ?perpLabel
ORDER BY DESC(?eventCount)
```

### Timeline of Events Against Specific Record

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc: <http://purl.org/dc/terms/>

SELECT ?event ?label ?type ?date ?severity WHERE {
    ?event a ex:HarmEvent ;
           rdfs:label ?label ;
           ex:harms ex:AuditLog2026Q2 ;
           ex:ofType ?harmType ;
           dc:date ?date .
    ?harmType rdfs:label ?type .
    OPTIONAL { ?event ex:severity ?severity }
}
ORDER BY ?date
```

## Pattern Analysis

### Identify Potential Cover-up Patterns

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?record ?recordLabel 
       (COUNT(DISTINCT ?suppressionEvent) as ?suppressions)
       (COUNT(DISTINCT ?alterationEvent) as ?alterations)
       (COUNT(DISTINCT ?denialEvent) as ?denials)
WHERE {
    ?record a ex:Record ;
            rdfs:label ?recordLabel .
    
    OPTIONAL {
        ?suppressionEvent ex:ofType ex:Suppression ;
                         ex:harms ?record .
    }
    OPTIONAL {
        ?alterationEvent ex:ofType ex:Alteration ;
                        ex:harms ?record .
    }
    OPTIONAL {
        ?denialEvent ex:ofType ex:Denial ;
                    ex:harms ?record .
    }
}
GROUP BY ?record ?recordLabel
HAVING (?suppressions > 0 && ?alterations > 0 && ?denials > 0)
```

## Aspect Analysis

### Aspect Attack Surface

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?aspect ?aspectLabel (COUNT(DISTINCT ?harm) as ?harmCount) WHERE {
    ?harm ex:targetsAspect ?aspect .
    ?aspect skos:prefLabel ?aspectLabel .
}
GROUP BY ?aspect ?aspectLabel
ORDER BY DESC(?harmCount)
```

### Multi-Aspect Harms

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label (COUNT(?aspect) as ?aspectCount) WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label ;
          ex:targetsAspect ?aspect .
}
GROUP BY ?harm ?label
HAVING (?aspectCount > 1)
ORDER BY DESC(?aspectCount)
```

## Detectability and Reversibility

### Difficult to Detect Harms

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label ;
          ex:detectability ex:DifficultToDetect .
}
```

### Irreversible Harms

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label ;
          ex:reversibility ex:Irreversible .
}
```

### Risk Matrix (Detectability × Reversibility)

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?harm ?label ?detectLabel ?reverseLabel WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label ;
          ex:detectability ?detect ;
          ex:reversibility ?reverse .
    ?detect skos:prefLabel ?detectLabel .
    ?reverse skos:prefLabel ?reverseLabel .
}
ORDER BY ?detectLabel ?reverseLabel
```

## Validation Queries

### Find Unclassified Harms

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label .
    FILTER NOT EXISTS { ?harm a ex:PrimeHarm }
    FILTER NOT EXISTS { ?harm a ex:CompositeHarm }
}
```

### Find Composites Without Dependencies

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:CompositeHarm ;
          rdfs:label ?label .
    FILTER NOT EXISTS { ?harm ex:buildsUpon ?dep }
}
```

### Find Harms Without Aspect Targeting

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?harm ?label WHERE {
    ?harm a ex:RecordHarm ;
          rdfs:label ?label .
    FILTER NOT EXISTS { ?harm ex:targetsAspect ?aspect }
}
```

## Advanced Queries

### Harm Propagation Analysis

Find all harms that could cascade from a prime harm:

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?prime ?primeLabel ?composite ?compositeLabel WHERE {
    ?prime a ex:PrimeHarm ;
           rdfs:label ?primeLabel .
    ?composite ex:buildsUpon+ ?prime ;
               rdfs:label ?compositeLabel .
}
ORDER BY ?primeLabel ?compositeLabel
```

### Event Clustering by Time Window

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?record (COUNT(?event) as ?eventCount) WHERE {
    ?event a ex:HarmEvent ;
           ex:harms ?record ;
           dc:date ?date .
    FILTER(?date >= "2026-05-01"^^xsd:date && 
           ?date <= "2026-05-31"^^xsd:date)
}
GROUP BY ?record
HAVING (?eventCount > 1)
```

### Severity Distribution

```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>

SELECT ?severity (COUNT(?event) as ?count) WHERE {
    ?event a ex:HarmEvent ;
           ex:severity ?severity .
}
GROUP BY ?severity
ORDER BY ?severity
```
