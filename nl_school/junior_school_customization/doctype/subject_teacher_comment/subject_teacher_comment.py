# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class SubjectTeacherComment(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        comment: DF.SmallText | None
        course: DF.Link | None
        course_name: DF.Data | None
        instructor: DF.Link | None
        instructor_name: DF.Data | None
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
    # end: auto-generated types

    pass
