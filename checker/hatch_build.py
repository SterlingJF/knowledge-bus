"""Include the canonical protocol and preset without maintaining a second authored copy."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

PRESET = "product-development"
PRESET_FILES = ("universe.kbp.yaml", "type-guidance.kbp.yaml")


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """Bundle the local protocol and preset copies, falling back to workspace sources."""
        root = Path(self.root)
        package = "src/kbp_conform" if self.target_name == "sdist" else "kbp_conform"
        name = "knowledge-bus-protocol.yaml"
        bundled = root / "src" / "kbp_conform" / name
        authority = root.parent / "protocol" / name
        protocol = bundled if bundled.is_file() else authority
        if not protocol.is_file():
            raise RuntimeError(
                "Missing protocol: build from the workspace or a complete source archive."
            )
        build_data["force_include"][str(protocol)] = f"{package}/{name}"
        bundled = root / "src" / "kbp_conform" / "presets" / PRESET
        authority = root.parent / "universes" / PRESET
        preset = bundled if (bundled / PRESET_FILES[0]).is_file() else authority
        if not all((preset / file).is_file() for file in PRESET_FILES):
            raise RuntimeError(
                "Missing preset: build from the workspace or a complete source archive."
            )
        for file in PRESET_FILES:
            build_data["force_include"][str(preset / file)] = (
                f"{package}/presets/{PRESET}/{file}"
            )
        license_file = root / "LICENSE"
        if not license_file.is_file():
            license_file = root.parent / "LICENSE"
        if self.target_name == "sdist" and license_file.is_file():
            build_data["force_include"][str(license_file)] = "LICENSE"
