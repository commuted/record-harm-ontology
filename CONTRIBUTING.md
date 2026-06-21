# Contributing to Record Harm Ontology

Thank you for your interest in contributing to the Record Harm Ontology project! This document provides guidelines for contributing.

## Ways to Contribute

### 1. Report Issues
- **Conceptual inconsistencies**: Found a logical problem in the taxonomy?
- **Missing harm types**: Identified a harm that doesn't fit existing categories?
- **Documentation gaps**: Something unclear or missing?

Open an issue with:
- Clear description of the problem
- Examples demonstrating the issue
- Suggested resolution (if applicable)

### 2. Propose New Harm Types

When proposing a new harm type, provide:

1. **Name and definition**: Clear, concise description
2. **Classification**: Is it Prime or Composite?
3. **Dependencies**: If Composite, which harms does it build upon?
4. **Aspects targeted**: Which of the 6 aspects does it attack?
5. **Real-world examples**: At least 2-3 concrete cases
6. **Detectability/Reversibility**: Your assessment with rationale

Example proposal format:
```markdown
## New Harm: [Name]

**Type**: [Prime/Composite]
**Builds Upon**: [If composite, list dependencies]
**Targets**: [List aspects]
**Detectability**: [Easy/Moderate/Difficult]
**Reversibility**: [Reversible/Partially/Irreversible]

**Definition**: [Clear description]

**Examples**:
1. [Real-world case 1]
2. [Real-world case 2]

**Rationale**: [Why this is distinct from existing harms]
```

### 3. Add Examples

Contribute real-world or realistic examples:
- Create TTL files in `examples/` directory
- Follow the pattern in `example-harm-events.ttl`
- Include context and documentation
- Anonymize sensitive information

### 4. Improve Documentation

- Fix typos or unclear explanations
- Add tutorials or guides
- Create visualization diagrams
- Translate documentation

### 5. Enhance SHACL Shapes

- Add new validation rules
- Improve error messages
- Add SPARQL-based constraints
- Test edge cases

## Development Process

### Setting Up

1. **Clone the repository**
```bash
git clone [repository-url]
cd record-harm-ontology
```

2. **Install dependencies**
```bash
pip install rdflib pyshacl
```

3. **Validate the ontology**
```bash
python scripts/validate.py
```

### Making Changes

1. **Create a branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Edit ontology files in `ontology/`
   - Update SHACL shapes in `shapes/` if needed
   - Add examples in `examples/`
   - Update documentation

3. **Validate your changes**
```bash
# Check OWL syntax
rapper -i turtle -o ntriples ontology/record-harm-ontology.ttl > /dev/null

# Run SHACL validation
python scripts/validate.py

# Run tests (if applicable)
pytest tests/
```

4. **Document your changes**
   - Update version comments in TTL files
   - Add entries to CHANGELOG.md
   - Update README.md if needed

5. **Commit with clear messages**
```bash
git add .
git commit -m "feat: Add [feature name]

- Detailed description
- Why this change is needed
- Any breaking changes"
```

### Commit Message Format

Follow conventional commits:
- `feat:` New feature or harm type
- `fix:` Bug fix or correction
- `docs:` Documentation changes
- `refactor:` Code restructuring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Pull Request Process

1. **Update documentation**: Ensure README and inline comments reflect changes
2. **Add tests**: If applicable, add validation tests
3. **Run validation**: Ensure all checks pass
4. **Create PR**: With clear description of changes
5. **Respond to feedback**: Address review comments promptly

## Ontology Design Principles

When contributing, follow these principles:

### 1. Ontological Clarity
- Each harm type must have a clear, distinct definition
- Avoid overlapping or redundant categories
- Maintain the Prime/Composite distinction rigorously

### 2. Formal Rigor
- Use OWL 2 DL constructs correctly
- Ensure SHACL shapes are consistent with OWL axioms
- Test with reasoners (HermiT, Pellet) when possible

### 3. Practical Utility
- Include worked examples for new concepts
- Consider real-world applicability
- Balance theoretical purity with practical usefulness

### 4. Documentation Quality
- Every class/property needs clear rdfs:comment
- Use skos:definition for harm instances
- Explain design decisions in inline comments

### 5. Backward Compatibility
- Avoid breaking changes when possible
- If breaking changes are necessary, document thoroughly
- Consider migration paths for existing users

## Code of Conduct

### Our Standards

- **Respectful**: Treat all contributors with respect
- **Constructive**: Provide helpful, actionable feedback
- **Collaborative**: Work together toward shared goals
- **Inclusive**: Welcome diverse perspectives and backgrounds

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing others' private information
- Other conduct inappropriate in a professional setting

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open an Issue
- **Security concerns**: Email [security contact]
- **Other inquiries**: Contact [maintainer email]

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Academic citations where appropriate

Thank you for helping improve the Record Harm Ontology!
