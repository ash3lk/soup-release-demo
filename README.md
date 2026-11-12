# Release pipeline report

[Repository](https://github.com/ash3lk/soup-release-demo) · [TestPyPI 0.9.4](https://test.pypi.org/project/soup-release-demo-shlyapik/0.9.4/)

## What wheel CI caught

Naive CI runs the tests against an editable install on Ubuntu with Python 3.12. Wheel CI runs Ruff, builds a wheel once, then tests it in clean environments on Ubuntu and Windows with Python 3.10, 3.11, and 3.12. It also tests the same wheel in Docker with Python 3.12.

| Bug | Why naive CI passed | Naive CI | Wheel CI |
| --- | --- | --- | --- |
| `StrEnum` import fails on Python 3.10 | Python 3.12 has `StrEnum`. | [Passed](https://github.com/ash3lk/soup-release-demo/actions/runs/43079195565) | [Failed](https://github.com/ash3lk/soup-release-demo/actions/runs/43079195635) |
| `pwd` import fails on Windows | Ubuntu has `pwd`. | [Passed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088967186) | [Failed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088967181) |
| `defaults.json` is missing from the wheel | An editable install reads it from the source tree. | [Passed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088973582) | [Failed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088973678) |
| `colorama` is missing from the runtime dependencies | The `dev` extra installs it. | [Passed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088981539) | [Failed](https://github.com/ash3lk/soup-release-demo/actions/runs/43088981547) |

Each row compares runs on the same commit. The missing JSON file surprised me most. I removed one line from `pyproject.toml`, and the editable tests still passed. Comparing the two wheel archives showed exactly what was missing.

After the fixes, CI passed on `main`. I published `v0.9.4` to TestPyPI through OIDC, downloaded it, and confirmed that both CLI tests passed in a clean environment. [Run on main](https://github.com/ash3lk/soup-release-demo/actions/runs/43169563494) · [Publish run](https://github.com/ash3lk/soup-release-demo/actions/runs/43170156775)

## Release checks

- The build job produces one wheel. The test and publish jobs download it by artifact ID.
- The build job checks the Git tag against the version inside the wheel. `v0.9.999` failed against wheel version `0.9.4`, so nothing was published. [Failed run](https://github.com/ash3lk/soup-release-demo/actions/runs/43169982177)
- PR checks have read-only repository access. Only the publish job gets `id-token: write`, and it runs on tag pushes in the `testpypi` environment. I haven't tested this with a real fork PR.

`colorama` is pinned to `0.4.6`, and the matrix and Docker installs use `--no-cache-dir`. The `build` tool is still resolved at run time, so rebuilding the same commit could pick up a different version. Dependency swaps and resolver-cache issues are still untested. [Runtime dependency](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/pyproject.toml#L9) · [Matrix install](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/scripts/check_wheel.py#L28) · [Docker install](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/Dockerfile#L4) · [Build workflow](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/.github/workflows/ci.yml#L21-L22)

The matrix leaves out Python 3.13+, macOS, ARM, and musl. CI builds the source distribution, but only installs, tests, and publishes the wheel. The publish action runs `twine check`, and there is no separate check of the wheel contents. The CLI tests cover `hello` and `show-config`. `--color` and invalid arguments are untested. [Publish action](https://github.com/pypa/gh-action-pypi-publish#disabling-metadata-verification)

Before publishing to PyPI, I'd keep manual approval, restrict who can create release tags, and require those tags to point to reviewed commits on `main`. I'd also pin Actions to commit SHAs.

## Proposed GPU checks on AWS

The CLI currently runs on CPU. I haven't built or tested the GPU setup. In this design, GitHub Actions assumes an IAM role through OIDC. Once the CPU checks pass, it uploads the tested wheel and its SHA-256 checksum to S3, then starts an AWS Batch job. The job verifies the checksum and installs the wheel on a `g4dn.xlarge` (one NVIDIA T4, 4 vCPUs). Batch scales to zero between runs. [AWS Batch GPU jobs](https://docs.aws.amazon.com/batch/latest/userguide/gpu-jobs.html)

| Run | What it checks | Monthly compute in Stockholm |
| --- | --- | --- |
| Release tag | Check CUDA execution and output. A failure blocks publishing. | 4 × 10 min on On-Demand at $0.558/h = $0.37 |
| Nightly on `main` | Try several input sizes and record runtime and peak GPU memory. | 30 × 15 min on Spot at $0.14/h = $1.05 |

The estimate comes to **$1.42/month** with five minutes of startup per job. At ten minutes of startup, it rises to $1.96. Running both jobs on On-Demand would cost $4.56. I used AWS console prices from November 12, 2026. The 30-day Spot averages ranged from $0.135 to $0.147/h across the three Stockholm zones. The estimate excludes storage, logs, and data transfer. [On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) · [Spot price history](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances-history.html)

I'd run one GPU job at a time, start with `nvidia-smi` and a single CUDA operation, and stop at the first failure. Nightly jobs can skip unchanged commits and retry once after a Spot interruption. I'd also set queue and job timeouts and add a budget alert. Before building this, I'd confirm Batch and `g4dn.xlarge` availability in `eu-north-1` and check that both On-Demand and Spot quotas allow at least four G/VT vCPUs. [EC2 quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) · [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)

## AI use and manual checks

I used Claude to plan the task, draft the CLI, tests, scripts, and workflows, review the workflows, and write the report and GPU estimate. I ran the commands, set up Trusted Publishing, checked the logs and AWS prices, and retested the downloaded release.

My first editable install failed because I ran it from `src/soup_demo` and the configured `src` path couldn't resolve there. I moved `pyproject.toml` to the repository root and reran the install. Later, a `sed` edit from Claude left two Ruff `PLW1510` errors. I added `check=False` to both calls with a targeted Python edit and checked the next CI run.
