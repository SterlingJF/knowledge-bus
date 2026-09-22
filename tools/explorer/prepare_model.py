"""Repository wrapper for installed Explorer model preparation."""

import sys

from kbp_conform import explorer as _explorer

MARK_SECTIONS = _explorer.MARK_SECTIONS
SOURCE_FIELD_A_SELF_CONTAINED_ARTIFACT_CANNOT_CARRY = (
    _explorer.SOURCE_FIELD_A_SELF_CONTAINED_ARTIFACT_CANNOT_CARRY
)
guidance_sections = _explorer.guidance_sections
prepare_marks = _explorer.prepare_marks
prepare_model = _explorer.prepare_model
main = _explorer.main


if __name__ == "__main__":
    sys.exit(main())
