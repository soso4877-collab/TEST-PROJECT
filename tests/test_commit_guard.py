"""저장소 공용 pre-commit 비밀정보 가드의 양방 회귀 테스트."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HOOK_SOURCE = ROOT / ".githooks" / "pre-commit"
BLOCK_MARKER = "COMMIT_SECRET_GUARD_BLOCKED"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """홈 설정을 읽지 않고 throwaway 저장소에서 Git 명령을 실행한다."""
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return subprocess.run(
        ["git", "-c", "core.excludesFile=", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
        check=False,
    )


def _require_ok(result: subprocess.CompletedProcess[str]) -> None:
    """준비 명령 실패는 훅 판정과 섞지 않고 즉시 드러낸다."""
    assert result.returncode == 0, result.stdout + result.stderr


def _new_repo(temp_root: Path) -> Path:
    """시스템 임시 영역에 훅이 배선된 독립 Git 저장소를 만든다."""
    assert HOOK_SOURCE.is_file(), "추적 가능한 .githooks/pre-commit이 필요합니다."
    repo = temp_root / "throwaway-repo"
    repo.mkdir()
    _require_ok(_git(repo, "init", "-q"))
    _require_ok(_git(repo, "config", "user.name", "Synthetic Tester"))
    _require_ok(_git(repo, "config", "user.email", "synthetic@example.invalid"))

    # 실제 훅 파일을 복사해 Git for Windows의 번들 sh 실행 경로까지 검증한다.
    hook_dir = repo / ".githooks"
    hook_dir.mkdir()
    copied_hook = hook_dir / "pre-commit"
    shutil.copy2(HOOK_SOURCE, copied_hook)
    copied_hook.chmod(copied_hook.stat().st_mode | stat.S_IXUSR)
    _require_ok(_git(repo, "config", "core.hooksPath", ".githooks"))
    return repo


@pytest.fixture
def guarded_repo() -> Iterator[Path]:
    """pytest의 저장소 내부 basetemp와 분리된 시스템 임시 저장소를 제공한다."""
    with tempfile.TemporaryDirectory(prefix="sajugen-commit-guard-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        assert not temp_root.is_relative_to(ROOT.resolve())
        yield _new_repo(temp_root)


def _commit(repo: Path, message: str = "synthetic commit") -> subprocess.CompletedProcess[str]:
    """현재 인덱스를 커밋해 Git이 pre-commit 훅을 실제 호출하게 한다."""
    return _git(repo, "commit", "-m", message)


def test_plain_staged_text_passes(guarded_repo: Path):
    repo = guarded_repo
    (repo / "plain.txt").write_text("ordinary staged text\n", encoding="utf-8")
    _require_ok(_git(repo, "add", "plain.txt"))

    result = _commit(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert BLOCK_MARKER not in result.stdout + result.stderr


def test_staged_pem_private_key_header_is_blocked(guarded_repo: Path):
    repo = guarded_repo
    pem_header = "-" * 5 + "BEGIN " + "PRIVATE KEY" + "-" * 5
    (repo / "synthetic.txt").write_text(
        f"{pem_header}\nSYNTHETIC-NOT-A-REAL-KEY\n",
        encoding="utf-8",
    )
    _require_ok(_git(repo, "add", "synthetic.txt"))

    result = _commit(repo)

    # `-s` 단독 실행 시 훅이 실제로 낸 차단 문구를 수동 증거로 노출한다.
    print((result.stdout + result.stderr).strip())
    assert result.returncode != 0
    assert BLOCK_MARKER in result.stdout + result.stderr


def test_staged_anthropic_key_shape_is_blocked(guarded_repo: Path):
    repo = guarded_repo
    synthetic_key = "sk-" + "ant-" + "synthetic_" * 4
    (repo / "settings.txt").write_text(
        f"ANTHROPIC_API_KEY={synthetic_key}\n",
        encoding="utf-8",
    )
    _require_ok(_git(repo, "add", "settings.txt"))

    result = _commit(repo)

    assert result.returncode != 0
    assert BLOCK_MARKER in result.stdout + result.stderr


def test_force_added_env_path_is_blocked(guarded_repo: Path):
    repo = guarded_repo
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / ".env").write_text("SYNTHETIC_ONLY=1\n", encoding="utf-8")
    _require_ok(_git(repo, "add", ".gitignore"))
    _require_ok(_git(repo, "add", "-f", ".env"))

    result = _commit(repo)

    assert result.returncode != 0
    assert BLOCK_MARKER in result.stdout + result.stderr


def test_repository_core_hooks_path_is_wired():
    if not (ROOT / ".git").exists():
        pytest.skip(".git이 없는 배포 아카이브에서는 로컬 Git 배선을 확인할 수 없습니다.")

    result = _git(ROOT, "config", "--local", "--get", "core.hooksPath")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == ".githooks"


def test_commit_message_and_document_mentions_pass(guarded_repo: Path):
    repo = guarded_repo
    (repo / "guard-notes.md").write_text(
        "`.env` 파일, 개인키, 삭제 명령은 정책 설명에서 언급할 수 있다.\n",
        encoding="utf-8",
    )
    _require_ok(_git(repo, "add", "guard-notes.md"))

    result = _commit(repo, "docs: .env와 개인키 및 삭제 명령 정책 설명")

    assert result.returncode == 0, result.stdout + result.stderr
    assert BLOCK_MARKER not in result.stdout + result.stderr


def test_env_example_path_passes(guarded_repo: Path):
    repo = guarded_repo
    (repo / ".env.example").write_text(
        "ANTHROPIC_API_KEY=replace_me\n",
        encoding="utf-8",
    )
    _require_ok(_git(repo, "add", ".env.example"))

    result = _commit(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert BLOCK_MARKER not in result.stdout + result.stderr
