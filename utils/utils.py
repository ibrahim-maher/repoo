# utils.py
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
import csv


def handle_batch_operations(request, model_class, redirect_url, fields_to_export=None, custom_export_handler=None):
    """
    Generic function to handle batch operations like delete and export for any model.

    Args:
        request: The HTTP request object
        model_class: The Django model class to operate on
        redirect_url: The URL to redirect to after delete operation
        fields_to_export: List of field names to export (if None, uses all model fields)
        custom_export_handler: Optional function to handle specialized export logic
            Function signature: f(request, selected_ids) -> HttpResponse

    Returns:
        HttpResponse for export or redirect for delete, or None if no action needed
    """
    if request.method != 'POST':
        return None

    action = request.POST.get('action')
    selected_ids = request.POST.getlist('selected_items')

    # Filter out empty strings or non-numeric values
    valid_ids = []
    for id_value in selected_ids:
        try:
            if id_value and id_value.strip():  # Check if not empty
                int(id_value)  # Check if convertible to int
                valid_ids.append(id_value)
        except (ValueError, TypeError):
            continue

    selected_ids = valid_ids

    if not selected_ids:
        messages.warning(request, "No valid items were selected.")
        return redirect(redirect_url)

    if action == 'delete':
        # Get the items to delete for the confirmation message
        items_to_delete = model_class.objects.filter(id__in=selected_ids)
        count = items_to_delete.count()

        # Delete the items
        items_to_delete.delete()

        # Show success message
        messages.success(request, f"{count} {model_class._meta.verbose_name_plural} have been deleted successfully.")
        return redirect(redirect_url)

    elif action == 'export':
        # Use custom export handler if provided
        if custom_export_handler is not None:
            return custom_export_handler(request, selected_ids)

        # Default export behavior
        # Get the queryset to export
        queryset = model_class.objects.filter(id__in=selected_ids)

        # Determine fields to export
        if fields_to_export is None:
            fields = [field.name for field in model_class._meta.fields]
        else:
            fields = fields_to_export

        # Create the HttpResponse with CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_class._meta.verbose_name_plural}.csv"'

        writer = csv.writer(response)

        # Write header row
        writer.writerow(fields)

        # Write data rows
        for obj in queryset:
            row = []
            for field in fields:
                # Handle nested attributes with double underscores (e.g., "user__email")
                if "__" in field:
                    parts = field.split("__")
                    value = obj
                    for part in parts:
                        if value is None:
                            break
                        value = getattr(value, part, None)
                else:
                    value = getattr(obj, field, None)

                # Handle callable fields
                if callable(value):
                    value = value()

                # Convert to string for CSV
                row.append(str(value) if value is not None else "")

            writer.writerow(row)

        return response

    return None