"""
This module provides some handy utilities for parsing and working with the specialized "path 
patterns" utilized by `yaml-extras` in the construction of `!import` tags.

The core abstraction provided by this module is the `PathPattern`, which is a custom implementation
of UNIX-like glob search on `pathlib.Path` objects, except that it also supports naming wildcard
globs so that their values can be extracted and referenced elsewhere. Some example valid path
patterns include:

``` yaml
# Use of anonymous * wildcard
- data/*.yml
# Use of anonymous ** wildcard
- data/**/*.yml
# Use of named wildcards
- data/{name:*}.yml
- data/{sub_path:**}/info.yml
- data/{name:*}/{sub_path:**}/{base_name:*}.yml
```

The results retrieved by a `PathPattern` are `PathWithMetadata` objects, which are a wrapper class
around `pathlib.Path` objects that also store optional metadata. This metadata is extracted from the
named wildcards in the pattern.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any


@dataclass
class PathWithMetadata:
    """Custom dataclass to store a Path object with optional metadata.

    Attributes:
        path (Path): Path object.
        metadata (Any): Optional metadata. Defaults to None.

    Methods:
        __hash__: Return the hash of the PathWithMetadata object, which is the hash of the path and
            string representation of the metadata.
    """

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
      - Only supports `*` and `**` wildcards.
      - Only officially supports selecting files, not directories.

    Enhancements:
      - Supports named wildcards with syntax `{name:*}` and `{name:**}`.

    Attributes:
        pattern (str): Pattern to match, using the supported `*` and `**` wildcards and named
            wildcards.
        relative_to (Path): Path to search for files. Defaults to None, which assumes the current
            working directory.

    Methods:
        __hash__: Return the hash of the PathPattern object, which is the hash of the string glob
            pattern.
        names: Return all named wildcards in the pattern.
        as_regex: Convert a pattern to a regular expression which should match all paths that match
            the UNIX glob pattern.
        glob_results: Return all paths that match the pattern using standard pathlib.Path.glob()
            method, returning simple Paths without metadata.
        results: Return all paths that match the pattern, including the metadata parsed from the
            named wildcards in the pattern.
    """

    pattern: str
    relative_to: Path | None = None

    def __hash__(self):
        return hash(self.pattern)

    @property
    def names(self) -> list[str]:
        """Return all named wildcards in the pattern. E.g., for the pattern `data/{name:*}.yml`, the
        only named wildcard is "name", so this method would return `["name"]`.

        Returns:
            list[str]: List of named wildcards.
        """
        return [match.group("name") for match in NAMED_WILDCARD_PATTERN.finditer(self.pattern)]

    @classmethod
    def as_regex(cls, pattern: str) -> re.Pattern:
        """Convert a pattern to a regular expression. The regular expression should match all paths
        that match the UNIX glob pattern, meaning that "*" wildcards match any character except
        slashes, and "**" wildcards match any characters including slashes.

        Args:
            pattern (str): Glob pattern to convert to a regex expression.

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
        """Return all paths that match the pattern using standard pathlib.Path.glob() method,
        returning simple Paths without metadata.

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
