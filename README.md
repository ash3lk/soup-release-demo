[REPORT.md](https://github.com/user-attachments/files/34747270/REPORT.md)
# Release pipeline report

[Repository](https://github.com/ash3lk/soup-release-demo) · [TestPyPI 0.9.4](https://test.pypi.org/project/soup-release-demo-shlyapik/0.9.4/)

## What the two workflows showed

`Naive CI` tested an editable install on Ubuntu with Python 3.12. `Wheel CI` runs Ruff, builds a wheel once, then installs it in a fresh virtual environment on Ubuntu and Windows with Python 3.10, 3.11, and 3.12. The same wheel also runs through both CLI tests in a Python 3.12 Docker container.

| Bug | Why naive CI passed | Naive CI (green) | Wheel CI (red) |
| --- | --- | --- | --- |
| `StrEnum` import on Python 3.10 | Python 3.12 has StrEnum | [Green run](https://github.com/ash3lk/soup-release-demo/actions/runs/43079195565) | [Red run](https://github.com/ash3lk/soup-release-demo/actions/runs/43079195635) |
| `pwd` import on Windows | Ubuntu has pwd | [Green run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088967186) | [Red run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088967181) |
| `defaults.json` missing from the wheel | The editable install reads the file from the source tree | [Green run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088973582) | [Red run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088973678) |
| Missing runtime dependency on `colorama` | The `dev` extra installed it for CI | [Green run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088981539) | [Red run](https://github.com/ash3lk/soup-release-demo/actions/runs/43088981547) |

Each row compares two runs on the same commit. [The fixed pipeline passed on main](https://github.com/ash3lk/soup-release-demo/actions/runs/43169563494), and [tag v0.9.4 published through OIDC](https://github.com/ash3lk/soup-release-demo/actions/runs/43170156775). I downloaded that version from TestPyPI and both CLI tests passed in a fresh environment.

## Release safeguards

- **Stale artifact.** The matrix, Docker job, and publish job all download the wheel by the artifact ID returned by `build`.
- **Wrong release version.** `build` compares the tag with `Version` inside the wheel. Wheel version 0.9.4 [failed the check for tag v0.9.999](https://github.com/ash3lk/soup-release-demo/actions/runs/43169982177), so publication was skipped.
- **Fork PR isolation.** PR checks have read-only repository permissions. Only `publish` has `id-token: write`, and it requires a tag push and the tag-restricted `testpypi` environment. This boundary is configured. I have yet to verify it with a fork PR run.

I chose these controls because a green test suite cannot tell the publisher which file, version, or identity it should use. The runtime dependency is `colorama==0.4.6`, and the matrix and Docker wheel installs pass `--no-cache-dir` to pip. Build tooling such as `build` still resolves at run time. Dependency substitution and resolver-cache failures remain open risks. [Runtime pin](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/pyproject.toml#L9) · [Matrix install](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/scripts/check_wheel.py#L28) · [Docker install](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/Dockerfile#L4) · [Build tooling](https://github.com/ash3lk/soup-release-demo/blob/c02acfb99a52b14b40645be0a731826512ad5941/.github/workflows/ci.yml#L21-L22)

## Coverage limits

- The matrix covers Ubuntu and Windows on Python 3.10–3.12. Python 3.13+, macOS, ARM, and musl are outside it.
- The source distribution is built as part of packaging. Installation tests and publication cover the wheel.
- The publishing action runs `twine check` before upload. The build has no standalone metadata or wheel-content checker. [Publish action](https://github.com/pypa/gh-action-pypi-publish#disabling-metadata-verification)
- The automated CLI tests cover `hello` and `show-config`. `--color`, invalid arguments, and behavior after later dependency changes are outside those checks.

## GPU CI on AWS (proposed)

The current CLI runs on CPU, so this is a design, not a tested pipeline. I chose AWS because GitHub Actions can assume a scoped IAM role through OIDC (no long-lived keys, the same principle as the TestPyPI publish), AWS Batch scales to zero between runs, and Spot capacity cuts the nightly bill. I chose Stockholm (eu-north-1) over us-east-1 because Spot is nearly half the price there; On-Demand is about 6% more expensive ($0.558 vs $0.526/h), and geography does not matter for an automated pipeline. After the CPU checks pass, Actions sends the tested wheel and its SHA-256 to S3 and submits an AWS Batch job. Batch verifies the checksum and installs the wheel on a `g4dn.xlarge` (one NVIDIA T4, 4 vCPU). [AWS Batch GPU jobs](https://docs.aws.amazon.com/batch/latest/userguide/gpu-jobs.html)

**Assumptions (none measured):** 4 releases and 30 nightly runs per month. Each run is 5 min of startup and image pull plus 5 min of tests (release) or 10 min of tests (nightly). Release runs on On-Demand at $0.558/h, nightly on Spot at $0.14/h.

| Run | Capacity | What it checks | Billed time per month |
| --- | --- | --- | --- |
| Release tag | On-Demand | Check CUDA execution and output. A failure blocks publication. | 4 × 10 min = 40 min |
| Nightly on main | Spot | Test several input sizes. Record time and peak GPU memory. | 30 × 15 min = 450 min |

**Estimated EC2 compute: $1.42/month** (release 40 min × $0.558/h = $0.37; nightly 450 min × $0.14/h = $1.05), versus $4.56 if everything ran On-Demand. Spot averages for g4dn.xlarge in the AWS console were $0.135, $0.147 and $0.136/h in the three zones (74–76% below On-Demand), which gives $1.38–$1.47/month. With 10 min of startup instead of 5, the total is about $1.96. The same model in us-east-1 gives $2.36, so the region saves under $1/month; most of the saving comes from running nightly on Spot. On-Demand and Spot prices were taken from the AWS console on 12 November 2026 (Spot: 30-day average). The us-east-1 rate and the interruption rates come from third-party trackers. Spot prices change. Storage, logs and data transfer are excluded. [EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/) · [Spot Price History](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances-history.html) · [Price tracker (eu-north-1)](https://www.doit.com/compute/spot/eu-north-1/g4dn.xlarge)

**Spot risk.** Trackers list a 15–20% interruption rate for g4dn.4xlarge in this region and above 20% for g4dn.2xlarge; I found no figure for g4dn.xlarge. Nightly runs may be interrupted, so one retry is allowed. Release runs stay On-Demand so a Spot shortage cannot block publication.

**Avoiding paid failures.** GPU jobs start only after the CPU pipeline is green. A short smoke test (nvidia-smi, one CUDA operation) runs before the long tests. Nightly is skipped if main has no new commits since the last successful GPU run. One job runs at a time and the pool scales to zero between runs. Queue and execution timeouts are set, the job stops on the first failed assertion, and it retries once at most, only after a Spot interruption. An AWS Budgets alert catches surprise spend. Before deployment, check the Stockholm vCPU quotas for G and VT instances (On-Demand and Spot are separate, per region): AWS lists zero as the default and a g4dn.xlarge needs four vCPUs. Also confirm in the console that AWS Batch and g4dn.xlarge are offered in eu-north-1. [EC2 quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) · [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)

## What broke along the way

My first editable install failed because I ran `pip install -e .` from `src/soup_demo`, where the configured `src` path did not exist. I moved `pyproject.toml` to the repository root and reran the command there. That made the install's working directory a useful first check when diagnosing a packaging error.

## Verdict and reflection

I would keep human approval for real PyPI. First, restrict release tag creation and require tags to point to reviewed main commits. Then pin Actions by commit SHA so the release runs the code I reviewed.

The packaging case stood out to me. Removing one line from `pyproject.toml` left the editable tests green while `defaults.json` disappeared from the wheel. Seeing the two archive listings made the difference tangible. I am still concerned that rebuilding the same commit later could pick up different build tooling.

## AI use

I used Claude throughout: to break down the task, draft the CLI, tests, helper scripts, and workflows, review the workflows, and write and revise this report, including the GPU cost section. I ran the commands, configured Trusted Publishing, checked the logs, and retested the downloaded release. One suggested `sed` edit did not fix the tests. Ruff still reported `PLW1510` twice. I switched to a targeted Python edit to add `check=False` in both calls and verified the next CI run. The first price figures for the GPU estimate came from third-party trackers; I then checked the eu-north-1 On-Demand and Spot prices in the AWS console, where Spot was slightly lower than the trackers showed.
