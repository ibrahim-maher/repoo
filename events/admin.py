from django.contrib import admin
from .models import Venue, Category, Event, Recurrence

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'venue', 'category')
    list_filter = ('start_date', 'end_date', 'venue', 'category')
    search_fields = ('name', 'description')

@admin.register(Recurrence)
class RecurrenceAdmin(admin.ModelAdmin):
    list_display = ('event', 'get_recurrence_rule')  # Update here
    search_fields = ('event__name', 'recurrence_rule')

    # Define a method to safely retrieve recurrence rule for display if it's not a direct field.
    def get_recurrence_rule(self, obj):
        return obj.recurrence_rule if hasattr(obj, 'recurrence_rule') else "N/A"
    get_recurrence_rule.short_description = 'Recurrence Rule'
