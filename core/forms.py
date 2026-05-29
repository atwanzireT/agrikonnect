from django import forms


TAILWIND_INPUT_CLASS = (
    "w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 "
    "text-sm text-gray-900 shadow-sm outline-none transition "
    "focus:border-green-600 focus:ring-2 focus:ring-green-200"
)

TAILWIND_SELECT_CLASS = (
    "w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 "
    "text-sm text-gray-900 shadow-sm outline-none transition "
    "focus:border-green-600 focus:ring-2 focus:ring-green-200"
)

TAILWIND_TEXTAREA_CLASS = (
    "w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 "
    "text-sm text-gray-900 shadow-sm outline-none transition "
    "focus:border-green-600 focus:ring-2 focus:ring-green-200"
)

TAILWIND_CHECKBOX_CLASS = "h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500"


def apply_tailwind_classes(form):
    for _, field in form.fields.items():
        widget = field.widget

        if isinstance(widget, forms.Textarea):
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{TAILWIND_TEXTAREA_CLASS} {existing}".strip()

        elif isinstance(widget, forms.SelectDateWidget):
            pass

        elif isinstance(widget, forms.Select):
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{TAILWIND_SELECT_CLASS} {existing}".strip()

        elif isinstance(widget, forms.CheckboxInput):
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{TAILWIND_CHECKBOX_CLASS} {existing}".strip()

        elif isinstance(widget, forms.ClearableFileInput):
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"block w-full text-sm text-gray-700 {existing}".strip()

        else:
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{TAILWIND_INPUT_CLASS} {existing}".strip()

        widget.attrs.setdefault("placeholder", field.label)
    return form