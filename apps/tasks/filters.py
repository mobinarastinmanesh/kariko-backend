import django_filters

from .models import Task


class TaskFilter(django_filters.FilterSet):
    list = django_filters.UUIDFilter(field_name="task_list_id")
    my_day = django_filters.BooleanFilter(field_name="my_day")
    important = django_filters.BooleanFilter(field_name="important")
    done = django_filters.BooleanFilter(field_name="done")
    planned = django_filters.BooleanFilter(method="filter_planned")
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")

    class Meta:
        model = Task
        fields = ["list", "my_day", "important", "done", "planned"]

    def filter_planned(self, queryset, name, value):
        if value:
            return queryset.filter(due_date__isnull=False)
        return queryset.filter(due_date__isnull=True)
