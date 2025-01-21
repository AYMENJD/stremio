from typing import Dict, List, Optional
from packaging.version import Version
from .exceptions import ManifestError

# https://github.com/Stremio/stremio-addon-linter/blob/master/lib/linter.js


def lint_manifest(manifest: Optional[Dict]) -> Dict:
    warnings: List[str] = []

    if not manifest or not isinstance(manifest, dict):
        raise ManifestError("manifest must be a dictionary")

    assert_string(
        manifest.get("id"),
        "manifest.id",
    )
    assert_string(
        manifest.get("name"),
        "manifest.name",
    )
    assert_semver(
        manifest.get("version"),
        "manifest.version",
    )

    assert_array(
        manifest.get("resources"),
        "manifest.resources",
    )
    if isinstance(manifest.get("resources"), list):
        resource_names = [
            r.get("name") if isinstance(r, dict) else r for r in manifest["resources"]
        ]
        warn_if_not_all_in_set(
            resource_names,
            ["catalog", "meta", "stream", "subtitles"],
            "manifest.resources",
            warnings,
        )

    assert_array(
        manifest.get("types"),
        "manifest.types",
    )
    assert_array(
        manifest.get("catalogs"),
        "manifest.catalogs",
    )

    # Optional idPrefixes
    if "idPrefixes" in manifest and manifest["idPrefixes"] is not None:
        assert_array(
            manifest["idPrefixes"],
            "manifest.idPrefixes",
        )

    # Behavior hints
    if "behaviorHints" in manifest:
        assert_object(
            manifest["behaviorHints"],
            "manifest.behaviorHints",
        )
        for prop_name in ["adult", "configurable", "configurationRequired", "p2p"]:
            if (
                isinstance(manifest["behaviorHints"], dict)
                and prop_name in manifest["behaviorHints"]
            ):
                assert_bool(
                    manifest["behaviorHints"][prop_name],
                    f"manifest.behaviorHints.{prop_name}",
                )

    # Validate catalogs
    if isinstance(manifest.get("catalogs"), list):
        for i, catalog in enumerate(manifest["catalogs"]):
            if not isinstance(catalog.get("id"), str) or not isinstance(
                catalog.get("type"), str
            ):
                raise ManifestError(
                    f"manifest.catalogs[{i}]: id and type must be string properties"
                )

            # Validate extra
            if "extra" in catalog:
                assert_array(
                    catalog["extra"],
                    f"manifest.catalogs[{i}].extra",
                )
                if isinstance(catalog["extra"], list):
                    for j, extra in enumerate(catalog["extra"]):
                        if "isRequired" in extra:
                            assert_bool(
                                extra["isRequired"],
                                f"manifest.catalogs[{i}].extra[{j}].isRequired",
                            )
                        assert_string(
                            extra.get("name"),
                            f"manifest.catalogs[{i}].extra[{j}].name",
                        )

            # Validate extraSupported and extraRequired
            if "extraSupported" in catalog:
                assert_array(
                    catalog["extraSupported"],
                    f"manifest.catalogs[{i}].extraSupported",
                )
            if "extraRequired" in catalog:
                assert_array(
                    catalog["extraRequired"],
                    f"manifest.catalogs[{i}].extraRequired",
                )

    return True


# Helper functions
def assert_string(value: Optional[str], name: str) -> None:
    if not isinstance(value, str):
        raise ManifestError(f"{name} must be a string")


def assert_bool(value: Optional[bool], name: str) -> None:
    if not isinstance(value, bool):
        raise ManifestError(f"{name} must be a boolean")


def assert_object(value: Optional[Dict], name: str) -> None:
    if not isinstance(value, dict):
        raise ManifestError(f"{name} must be a dictionary")


def assert_array(value: Optional[List], name: str) -> None:
    if not isinstance(value, list):
        raise ManifestError(f"{name} must be a list")


def assert_semver(value: Optional[str], name: str) -> None:
    if not isinstance(value, str):
        raise ManifestError(f"{name} must be a valid version string")

    try:
        Version(value)
    except Exception:
        raise ManifestError(f"{name} must be a valid version string")


def warn_if_not_all_in_set(
    values: Optional[List], valid_set: List[str], name: str, warnings: List[str]
) -> None:
    if not isinstance(values, list):
        return
    for value in values:
        if value not in valid_set:
            warnings.append(f"{name}: unknown value {value}")
