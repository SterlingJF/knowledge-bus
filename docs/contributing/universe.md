# Universe Contributions

For one subject, a universe lists the questions each kind of document should answer. Its guidance says how to answer those questions well. This path suits domain experts, researchers and writers. You do not need to code.

## When to Open an Issue First

To change what a definition asks or means, open a [universe issue](https://github.com/SterlingJF/knowledge-bus/issues/new?template=universe.yml) first:

1. Describe a real case where the current wording misleads or leaves something out. Leave out names.
2. Fill in the Current | Proposed table, one row per changed line.
3. Name a published source for any advice that follows an outside standard.

For example:

| Current | Proposed |
| --- | --- |
| Can this step be undone, and at what cost? | Can this step be undone, and what would undoing it cost? |

If you add, remove or redefine a value under `frames:`, such as the `design` stage, say so in the issue. The eval cases for it need new labels.

Fix a typo or broken link in a pull request.

## What You Can Change

You can change the definitions and guidance in `universes/codebase-recordkeeping/` and `universes/product-development/`, and the explorer map icons in `universes/product-development/`.

Never reuse a definition's code, and never give a code to a different definition.

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

## Proof to Bring

One change in meaning per pull request.

- [ ] New definitions: codes from `just mint <kind> <count>`.
- [ ] Advice from a published standard: add the standard under `sources:` at the top of the guidance file, and cite it in the advice.
- [ ] `uv run kbp` passes.
- [ ] Rebuilt and included: `just skills-build`.
- [ ] For `universes/product-development/`, also rebuilt and included: `just explorer-gallery` and the explorer data command below.
- [ ] [Checks every pull request needs](../../CONTRIBUTING.md#every-pull-request).

```sh
uv run --locked python tools/explorer/prepare_model.py --input universes/product-development/universe.kbp.yaml --guidance universes/product-development/type-guidance.kbp.yaml --marks universes/product-development/marks.explorer.yaml --output explorer/test/fixtures/product-development.json
```

Maintainers run the paid wording checks after a first review.

## Handing Over

Under "Who builds the change" in the issue, say whether you will build the change or someone else. If someone else builds it, they credit you as a co-author.

## Deeper Reading

- [Adapting the Example](../adapting-the-example.md) — minting codes and citing sources.
- [Product Development Universe Evolution](../research-product-development-universe-evolution-2026-09-15.md) — a past change in meaning.
- [Code Repository Universe Research](../research-code-repository-universe-2026-10-08.md) — the corpus, counts and sources behind the codebase-recordkeeping definitions.
- [Evals](../../evals/README.md) — how wording is graded.
