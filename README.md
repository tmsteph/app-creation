# Human — a human-first, agent-native language experiment

Most programming languages make people describe *machine mechanics*. Human explores a smaller surface: describe the application's data, events, state changes, and intentions, then compile that into ordinary inspectable code.

This repository is deliberately a tiny experiment, not a claim that English can replace programming.

## Example

```human
app GarageCRM

data Customer:
    name
    email
    status = "lead"

when Customer is created:
    send welcome email
    notify sales

when payment succeeds:
    Customer.status = "client"
    create project
```

Human v0 treats unfamiliar event statements such as `send welcome email` as explicit runtime actions. State assignments are compiled directly. Nothing requires an AI model at runtime.

## Try it

```bash
python compiler.py examples/garage.human -o build/garage.py
python -m unittest discover -s tests
python benchmark.py
```

## Design rules

1. **Human-readable first.** A non-programmer should be able to follow the main program flow.
2. **Strict meaning.** The compiler rejects ambiguity rather than asking a model to guess at runtime.
3. **Inspectable output.** v0 compiles to boring Python.
4. **AI optional.** Agents may author or modify Human, but deployed programs do not need an LLM.
5. **Small semantic surface.** Prefer built-in concepts for data, events, effects, persistence, networking, concurrency, and recovery over libraries full of glue code.
6. **AST-friendly.** Agents should eventually edit structured program nodes rather than repeatedly rewriting whole files.
7. **Measure it.** Compare source size, implementation time, model tokens, retries, test pass rate, and eventually energy against conventional implementations.

## What v0 actually supports

- `app Name`
- `data Name:` blocks with fields and literal defaults
- `when event name:` blocks
- `Entity.field = literal` state changes
- free-form action lines passed to a tiny runtime action hook
- compilation to dependency-free Python

It intentionally does **not** yet implement persistence, networking, concurrency, natural-language interpretation, static types, or automatic deployment.

## Benchmark hypothesis

The useful hypothesis is not “less code is always better.” It is:

> For common application workflows, a smaller and more constrained source language can reduce the amount of text and search an agent must generate, inspect, and repair while preserving human readability and deterministic execution.

`benchmark.py` currently measures only source lines and bytes for a toy Garage CRM example. Future experiments should record agent input/output tokens, wall-clock time, retries, tests passed, and estimated compute across identical tasks.

## Next experiment

Build the same small CRM workflow three ways:

- Human
- Python
- TypeScript

Give a coding agent identical change requests (add validation, add an event, rename a field, introduce a failure/retry rule) and record how much work is required in each representation.
