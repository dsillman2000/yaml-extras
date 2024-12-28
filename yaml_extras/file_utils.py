from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any


@dataclass
class PathWithMetadata:
    """Custom dataclass to store a Path object with optional metadata."""

    path: Path
    metadata: Any = None

    def __hash__(self):
        return hash((self.path, str(self.metadata)))


NAMED_WILDCARD_PATTERN: re.Pattern = re.compile(r"\{(?P<name>\w+):(?P<wildcard>\*\*?)\}")
REGEX_COUNTERPART: dict[str, str] = {
    "*": r"[^/]*",
    "**": r"(?:[^/]*/?)*[^/]*",
}


@dataclass
class PathPattern:
    """Custom implementation of unix-like glob search on pathlib.Path objects. Returned paths may
    include metadata as PathWithMetadata dataclasses.

    Limitations:
      - Only supports '*' and '**' wildcards.
      - Only officially supports selecting files, not directories.

    Enhancements:
      - Supports named wildcards with syntax '{name:*}' and '{name:**}'.
    """

    pattern: str
    relative_to: Path | None = None

    def __hash__(self):
        return hash(self.pattern)

    @property
    def names(self) -> list[str]:
        """Return all named wildcards in the pattern.

        Returns:
            list[str]: List of named wildcards.
        """
        return [match.group("name") for match in NAMED_WILDCARD_PATTERN.finditer(self.pattern)]

    @classmethod
    def as_regex(cls, pattern: str) -> re.Pattern:
        """Convert a pattern to a regular expression.

        Args:
            pattern (str): Pattern to convert.

        Returns:
            re.Pattern: Compiled regular expression object.
        """
        global NAMED_WILDCARD_PATTERN, REGEX_COUNTERPART

        def replace_named_globs(match: re.Match[str]):
            # Extract the name and wildcard type
            name = match.group("name")
            wildcard = match.group("wildcard")
            # Map wildcards to regex equivalents
            try:
                return r"(?P<" + name + r">" + REGEX_COUNTERPART[wildcard] + r")"
            except KeyError:
                raise ValueError(f"Unsupported wildcard: {wildcard}")

        # Replace named globs
        processed = NAMED_WILDCARD_PATTERN.sub(replace_named_globs, pattern)

        escaped = re.escape(processed)
        re_pattern = escaped.replace(r"\*\*", REGEX_COUNTERPART["**"]).replace(r"\.\*", ".*")
        re_pattern = re_pattern.replace(r"\*", REGEX_COUNTERPART["*"])
        re_pattern = (
            re_pattern.replace(r"\?", "?")
            .replace(r"\*", "*")
            .replace(r"\[", "[")
            .replace(r"\]", "]")
            .replace(r"\^", "^")
            .replace(r"\$", "$")
            .replace(r"\(", "(")
            .replace(r"\)", ")")
        )

        re_pattern = f"{re_pattern}$"
        return re.compile(re_pattern)

    @lru_cache
    def glob_results(self) -> list[Path]:
        """Return all paths that match the pattern using standard pathlib.Path.glob() method, returning
        simple Paths without metadata.

        Returns:
            list[Path]: List of pathlib.Path objects matching the pattern.
        """
        global NAMED_WILDCARD_PATTERN
        pattern_without_names = re.sub(NAMED_WILDCARD_PATTERN, r"\2", self.pattern)
        relative_to = self.relative_to or Path.cwd()
        return list(relative_to.glob(pattern_without_names))

    @lru_cache
    def results(self) -> list[PathWithMetadata]:
        """Return all paths that match the pattern, including metadata.

        Returns:
            list[PathWithMetadata]: List of PathWithMetadata objects matching the pattern.
        """
        paths_to_metadata: dict[Path, Any] = {path: None for path in self.glob_results()}
        for path in paths_to_metadata.keys():
            if match := PathPattern.as_regex(self.pattern).search(str(path)):
                paths_to_metadata[path] = match.groupdict() or None
        return [PathWithMetadata(path, meta) for path, meta in paths_to_metadata.items()]
