"""Include the canonical protocol without maintaining a second authored copy."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """Bundle the local protocol copy, falling back to workspace sources."""
        root = Path(self.root)
        name = "knowledge-bus-protocol.yaml"
        bundled = root / "src" / "kbp_conform" / name
        authority = root.parent / "protocol" / name
        protocol = bundled if bundled.is_file() else authority
        if not protocol.is_file():
            raise RuntimeError(
                "Missing protocol: build from the workspace or a complete source archive."
            )
        destination = (
            f"src/kbp_conform/{name}"
            if self.target_name == "sdist"
            else f"kbp_conform/{name}"
        )
        build_data["force_include"][str(protocol)] = destination
        license_file = root / "LICENSE"
        if not license_file.is_file():
            license_file = root.parent / "LICENSE"
        if self.target_name == "sdist" and license_file.is_file():
            build_data["force_include"][str(license_file)] = "LICENSE"
