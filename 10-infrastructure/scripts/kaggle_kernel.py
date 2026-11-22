"""Write a Kaggle script kernel that runs one command from this repo at one exact commit.

    python 10-infrastructure/scripts/kaggle_kernel.py --user <kaggle-user> --run tr1-20261123-smoke \
        --cmd "python 04-training/scripts/smoke.py --steps 2000"
    kaggle kernels push -p runs/kernels/tr1-20261123-smoke

The kernel clones the public repo, checks out the commit, installs requirements-kaggle.txt (Kaggle's own torch is kept)
and runs the command. HF_TOKEN comes from a Kaggle secret of that name. Pushing again starts the next session; the
run resumes from its latest checkpoint. Not yet run on Kaggle: it needs a Kaggle account and the Hub repos.
"""
import argparse
import json
import pathlib
import re
import subprocess

REPO = "https://github.com/TEJASKUMAR-REDDY-J/Formant.git"
MAIN = '''import os, subprocess
def sh(*a, **k): subprocess.run(a, check=True, **k)
try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
except Exception as e:
    print("HF_TOKEN secret not available:", e)
sh("git", "clone", "--filter=blob:none", {repo!r}, "/kaggle/working/formant")
os.chdir("/kaggle/working/formant")
sh("git", "checkout", {commit!r})
sh("pip", "install", "-q", "-r", "requirements-kaggle.txt")
env = dict(os.environ, PYTHONPATH="src", FORMANT_RUN={run!r}, FORMANT_COMMIT={commit!r})
sh("bash", "-lc", {cmd!r}, env=env)
'''


def build(user, run, cmd, commit, root="runs/kernels"):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", run):
        raise ValueError(f"run name must be lower-case words joined by hyphens: {run}")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("commit must be a full 40-hex hash")
    d = pathlib.Path(root) / run
    d.mkdir(parents=True, exist_ok=True)
    (d / "main.py").write_text(MAIN.format(repo=REPO, commit=commit, run=run, cmd=cmd))
    (d / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{run}", "title": run, "code_file": "main.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": []}, indent=1))
    compile((d / "main.py").read_text(), "main.py", "exec")
    return d


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    for n in ("user", "run", "cmd"):
        a.add_argument("--" + n, required=True)
    args = a.parse_args()
    git = lambda *x: subprocess.run(["git", *x], check=True, capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("uncommitted changes: the kernel runs a commit, so commit (and push) first")
    print("wrote", build(args.user, args.run, args.cmd, git("rev-parse", "HEAD")))
