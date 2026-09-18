"""Local persistent storage for the VEXION Beta.

This module intentionally exposes a small Mongo-like async API so the existing
routers can use the same storage interface while VEXION is in local Beta.

Production storage can replace this module later without requiring every router
to be rewritten.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / ".vexion-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_COLLECTIONS = (
    "users",
    "conversations",
    "messages",
    "projects",
    "attachments",
    "api_keys",
    "waitlist",
    "status_checks",
)

_LOCK = asyncio.Lock()


def _default_path(collection: str) -> Path:
    return DATA_DIR / f"{collection}.json"


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return {
            "__vexion_type__": "datetime",
            "value": value.isoformat(),
        }

    if isinstance(value, date):
        return {
            "__vexion_type__": "date",
            "value": value.isoformat(),
        }

    return str(value)


def _json_restore(value: Any) -> Any:
    if isinstance(value, dict):
        marker = value.get("__vexion_type__")

        if marker == "datetime":
            try:
                return datetime.fromisoformat(value["value"])
            except Exception:
                return value["value"]

        if marker == "date":
            try:
                return date.fromisoformat(value["value"])
            except Exception:
                return value["value"]

        return {
            key: _json_restore(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_json_restore(item) for item in value]

    return value


def _read_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        restored = _json_restore(raw)

        if isinstance(restored, list):
            return restored

        return []
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Could not read local collection %s: %s", path, exc)
        return []


def _write_file(path: Path, documents: List[Dict[str, Any]]) -> None:
    temporary = path.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(
            documents,
            handle,
            default=_json_default,
            ensure_ascii=False,
            indent=2,
        )

    temporary.replace(path)


def _get_path(document: Dict[str, Any], path: str) -> Any:
    current: Any = document

    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None

        current = current[part]

    return current


_MISSING = object()


def _get_path_with_missing(document: Dict[str, Any], path: str) -> Any:
    current: Any = document

    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return _MISSING

        current = current[part]

    return current


def _set_path(document: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = document

    for part in parts[:-1]:
        existing = current.get(part)

        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing

        current = existing

    current[parts[-1]] = value


def _unset_path(document: Dict[str, Any], path: str) -> None:
    parts = path.split(".")
    current: Any = document

    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return

        current = current[part]

    if isinstance(current, dict):
        current.pop(parts[-1], None)


def _equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, datetime) and isinstance(expected, str):
        try:
            expected = datetime.fromisoformat(expected)
        except ValueError:
            pass

    return actual == expected


def _compare(actual: Any, expected: Any, operator: str) -> bool:
    if actual is _MISSING:
        return False

    if operator == "$in":
        if not isinstance(expected, list):
            return False

        if isinstance(actual, list):
            return any(
                any(_equal(item, candidate) for candidate in expected)
                for item in actual
            )

        return any(_equal(actual, candidate) for candidate in expected)

    if operator == "$nin":
        if not isinstance(expected, list):
            return True

        if isinstance(actual, list):
            return not any(
                any(_equal(item, candidate) for candidate in expected)
                for item in actual
            )

        return not any(_equal(actual, candidate) for candidate in expected)

    if operator == "$exists":
        return (actual is not _MISSING) == bool(expected)

    if operator == "$ne":
        return not _equal(actual, expected)

    if operator == "$gte":
        try:
            return actual >= expected
        except TypeError:
            return False

    if operator == "$gt":
        try:
            return actual > expected
        except TypeError:
            return False

    if operator == "$lte":
        try:
            return actual <= expected
        except TypeError:
            return False

    if operator == "$lt":
        try:
            return actual < expected
        except TypeError:
            return False

    return False


def _matches(document: Dict[str, Any], query: Optional[Dict[str, Any]]) -> bool:
    if not query:
        return True

    for key, expected in query.items():
        if key == "$or":
            if not isinstance(expected, list):
                return False

            if not any(_matches(document, item) for item in expected):
                return False

            continue

        if key == "$and":
            if not isinstance(expected, list):
                return False

            if not all(_matches(document, item) for item in expected):
                return False

            continue

        actual = _get_path_with_missing(document, key)

        if isinstance(expected, dict) and any(
            str(k).startswith("$") for k in expected
        ):
            for operator, operand in expected.items():
                if not _compare(actual, operand, operator):
                    return False

            continue

        if actual is _MISSING or not _equal(actual, expected):
            return False

    return True


def _apply_projection(
    document: Dict[str, Any],
    projection: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not projection:
        return copy.deepcopy(document)

    includes = [
        key for key, value in projection.items()
        if value and key != "_id"
    ]

    excludes = [
        key for key, value in projection.items()
        if not value
    ]

    if includes:
        result: Dict[str, Any] = {}

        for key in includes:
            value = _get_path_with_missing(document, key)

            if value is not _MISSING:
                _set_path(result, key, copy.deepcopy(value))

        if projection.get("_id") and "_id" in document:
            result["_id"] = copy.deepcopy(document["_id"])

        return result

    result = copy.deepcopy(document)

    for key in excludes:
        _unset_path(result, key)

    return result


class LocalCursor:
    def __init__(
        self,
        documents: Iterable[Dict[str, Any]],
    ) -> None:
        self._documents = [
            copy.deepcopy(document)
            for document in documents
        ]

    def sort(self, key_or_spec: Any, direction: Optional[int] = None):
        if isinstance(key_or_spec, str):
            specs = [(key_or_spec, direction or 1)]
        else:
            specs = list(key_or_spec)

        # Stable sorting from the least significant field to the most
        # significant field.
        for key, order in reversed(specs):
            reverse = order < 0

            def sort_key(document: Dict[str, Any], field=key):
                value = _get_path(document, field)

                if value is None:
                    return (0, "")
                return (1, value)

            try:
                self._documents.sort(
                    key=sort_key,
                    reverse=reverse,
                )
            except TypeError:
                self._documents.sort(
                    key=lambda document, field=key: str(
                        _get_path(document, field)
                    ),
                    reverse=reverse,
                )

        return self

    def limit(self, amount: int):
        self._documents = self._documents[:amount]
        return self

    def skip(self, amount: int):
        self._documents = self._documents[amount:]
        return self

    async def to_list(self, length: Optional[int] = None):
        if length is None or length < 0:
            return copy.deepcopy(self._documents)

        return copy.deepcopy(self._documents[:length])


class LocalCollection:
    def __init__(
        self,
        store: "LocalDatabase",
        name: str,
    ) -> None:
        self.store = store
        self.name = name

    async def _documents(self) -> List[Dict[str, Any]]:
        return self.store._read_collection(self.name)

    async def find_one(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        async with _LOCK:
            documents = await self._documents()

            for document in documents:
                if _matches(document, query):
                    return _apply_projection(
                        document,
                        projection,
                    )

        return None

    def find(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
    ) -> LocalCursor:
        documents = self.store._read_collection(self.name)

        matched = [
            _apply_projection(document, projection)
            for document in documents
            if _matches(document, query)
        ]

        return LocalCursor(matched)

    async def insert_one(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with _LOCK:
            documents = await self._documents()
            documents.append(copy.deepcopy(document))
            self.store._write_collection(
                self.name,
                documents,
            )

        return {
            "inserted_id": document.get("id"),
        }

    async def insert_many(
        self,
        documents_to_insert: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        items = [
            copy.deepcopy(document)
            for document in documents_to_insert
        ]

        async with _LOCK:
            documents = await self._documents()
            documents.extend(items)
            self.store._write_collection(
                self.name,
                documents,
            )

        return {
            "inserted_ids": [
                document.get("id")
                for document in items
            ],
        }

    async def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> Dict[str, Any]:
        async with _LOCK:
            documents = await self._documents()

            for index, document in enumerate(documents):
                if not _matches(document, query):
                    continue

                updated = _apply_update(
                    document,
                    update,
                )

                documents[index] = updated
                self.store._write_collection(
                    self.name,
                    documents,
                )

                return {
                    "matched_count": 1,
                    "modified_count": 1,
                }

            if upsert:
                base = {
                    key: copy.deepcopy(value)
                    for key, value in query.items()
                    if not key.startswith("$")
                    and not (
                        isinstance(value, dict)
                        and any(
                            str(k).startswith("$")
                            for k in value
                        )
                    )
                }

                created = _apply_update(
                    base,
                    update,
                )

                documents.append(created)
                self.store._write_collection(
                    self.name,
                    documents,
                )

                return {
                    "matched_count": 0,
                    "modified_count": 0,
                    "upserted_id": created.get("id"),
                }

        return {
            "matched_count": 0,
            "modified_count": 0,
        }

    async def update_many(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> Dict[str, Any]:
        async with _LOCK:
            documents = await self._documents()
            matched = 0

            for index, document in enumerate(documents):
                if not _matches(document, query):
                    continue

                documents[index] = _apply_update(
                    document,
                    update,
                )
                matched += 1

            if matched:
                self.store._write_collection(
                    self.name,
                    documents,
                )

            elif upsert:
                base = {
                    key: copy.deepcopy(value)
                    for key, value in query.items()
                    if not key.startswith("$")
                }

                created = _apply_update(
                    base,
                    update,
                )

                documents.append(created)
                self.store._write_collection(
                    self.name,
                    documents,
                )

                return {
                    "matched_count": 0,
                    "modified_count": 0,
                    "upserted_id": created.get("id"),
                }

            return {
                "matched_count": matched,
                "modified_count": matched,
            }

    async def find_one_and_update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        return_document: Any = False,
        upsert: bool = False,
    ) -> Optional[Dict[str, Any]]:
        async with _LOCK:
            documents = await self._documents()

            for index, document in enumerate(documents):
                if not _matches(document, query):
                    continue

                before = copy.deepcopy(document)
                after = _apply_update(
                    document,
                    update,
                )

                documents[index] = after
                self.store._write_collection(
                    self.name,
                    documents,
                )

                selected = after if return_document else before

                return _apply_projection(
                    selected,
                    projection,
                )

            if upsert:
                base = {
                    key: copy.deepcopy(value)
                    for key, value in query.items()
                    if not key.startswith("$")
                }

                created = _apply_update(
                    base,
                    update,
                )

                documents.append(created)
                self.store._write_collection(
                    self.name,
                    documents,
                )

                return _apply_projection(
                    created,
                    projection,
                )

        return None

    async def delete_one(
        self,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with _LOCK:
            documents = await self._documents()

            for index, document in enumerate(documents):
                if _matches(document, query):
                    documents.pop(index)
                    self.store._write_collection(
                        self.name,
                        documents,
                    )

                    return {
                        "deleted_count": 1,
                    }

        return {
            "deleted_count": 0,
        }

    async def delete_many(
        self,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with _LOCK:
            documents = await self._documents()

            remaining = [
                document
                for document in documents
                if not _matches(document, query)
            ]

            deleted = len(documents) - len(remaining)

            if deleted:
                self.store._write_collection(
                    self.name,
                    remaining,
                )

            return {
                "deleted_count": deleted,
            }

    async def count_documents(
        self,
        query: Optional[Dict[str, Any]] = None,
    ) -> int:
        documents = self.store._read_collection(self.name)

        return sum(
            1
            for document in documents
            if _matches(document, query)
        )

    async def distinct(
        self,
        field: str,
        query: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        documents = self.store._read_collection(self.name)
        values: List[Any] = []

        for document in documents:
            if not _matches(document, query):
                continue

            value = _get_path(document, field)

            if value not in values:
                values.append(copy.deepcopy(value))

        return values

    def aggregate(
        self,
        pipeline: List[Dict[str, Any]],
    ) -> LocalCursor:
        documents = self.store._read_collection(self.name)

        for stage in pipeline:
            if "$match" in stage:
                query = stage["$match"]
                documents = [
                    document
                    for document in documents
                    if _matches(document, query)
                ]

            elif "$group" in stage:
                documents = _aggregate_group(
                    documents,
                    stage["$group"],
                )

            elif "$sort" in stage:
                cursor = LocalCursor(documents)
                cursor.sort(
                    list(stage["$sort"].items())
                )
                documents = cursor._documents

            elif "$limit" in stage:
                documents = documents[: int(stage["$limit"])]

            elif "$skip" in stage:
                documents = documents[int(stage["$skip"]):]

        return LocalCursor(documents)


def _apply_update(
    document: Dict[str, Any],
    update: Dict[str, Any],
) -> Dict[str, Any]:
    result = copy.deepcopy(document)

    if "$set" in update:
        for key, value in update["$set"].items():
            _set_path(
                result,
                key,
                copy.deepcopy(value),
            )

    if "$unset" in update:
        for key in update["$unset"]:
            _unset_path(result, key)

    if "$inc" in update:
        for key, value in update["$inc"].items():
            current = _get_path(result, key)

            if current is None:
                current = 0

            _set_path(
                result,
                key,
                current + value,
            )

    if "$push" in update:
        for key, value in update["$push"].items():
            current = _get_path(result, key)

            if not isinstance(current, list):
                current = []

            current.append(copy.deepcopy(value))
            _set_path(result, key, current)

    # Support plain document replacement as well.
    if not any(
        key.startswith("$")
        for key in update
    ):
        result = copy.deepcopy(update)

    return result


def _aggregate_group(
    documents: List[Dict[str, Any]],
    specification: Dict[str, Any],
) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}

    group_id_expression = specification.get("_id")

    for document in documents:
        if isinstance(group_id_expression, str) and group_id_expression.startswith("$"):
            group_id = _get_path(
                document,
                group_id_expression[1:],
            )
        else:
            group_id = group_id_expression

        key = json.dumps(
            group_id,
            default=_json_default,
            sort_keys=True,
        )

        if key not in groups:
            groups[key] = {
                "_id": copy.deepcopy(group_id),
            }

            for field, expression in specification.items():
                if field != "_id" and isinstance(expression, dict):
                    if "$sum" in expression:
                        groups[key][field] = 0

        target = groups[key]

        for field, expression in specification.items():
            if field == "_id" or not isinstance(expression, dict):
                continue

            if "$sum" not in expression:
                continue

            operand = expression["$sum"]

            if isinstance(operand, (int, float)):
                value = operand

            elif isinstance(operand, dict) and "$ifNull" in operand:
                source, fallback = operand["$ifNull"]

                if isinstance(source, str) and source.startswith("$"):
                    value = _get_path(
                        document,
                        source[1:],
                    )
                else:
                    value = source

                if value is None:
                    value = fallback

            elif isinstance(operand, str) and operand.startswith("$"):
                value = _get_path(
                    document,
                    operand[1:],
                )
            else:
                value = 0

            try:
                target[field] += value or 0
            except TypeError:
                pass

    return list(groups.values())


class LocalDatabase:
    def __init__(self) -> None:
        self._collections: Dict[str, LocalCollection] = {
            name: LocalCollection(self, name)
            for name in _COLLECTIONS
        }

    def __getattr__(self, name: str) -> LocalCollection:
        if name.startswith("_"):
            raise AttributeError(name)

        if name not in self._collections:
            self._collections[name] = LocalCollection(
                self,
                name,
            )

        return self._collections[name]

    def _read_collection(
        self,
        name: str,
    ) -> List[Dict[str, Any]]:
        return _read_file(
            _default_path(name)
        )

    def _write_collection(
        self,
        name: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        _write_file(
            _default_path(name),
            documents,
        )


db = LocalDatabase()


class LocalClient:
    """Compatibility object for the old server lifespan."""

    def close(self) -> None:
        return None


client = LocalClient()


async def ensure_indexes() -> None:
    """No-op compatibility hook.

    Local JSON storage has no database indexes. This remains async so the
    existing startup lifecycle can stay simple.
    """

    return None
